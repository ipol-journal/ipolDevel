import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

export function simplifyLongtables(text) {
  let pos = 0;
  while (true) {
    const idx = text.indexOf("\\begin{longtable}", pos);
    if (idx === -1) {
      break;
    }
    const braceIdx = text.indexOf("{", idx + "\\begin{longtable}".length);
    if (braceIdx === -1) {
      pos = idx + 1;
      continue;
    }
    let depth = 1;
    let i = braceIdx + 1;
    while (i < text.length && depth > 0) {
      if (text[i] === "{") {
        depth++;
      } else if (text[i] === "}") {
        depth--;
      }
      i++;
    }
    if (depth === 0) {
      text = text.substring(0, braceIdx) + "{llc}" + text.substring(i);
      pos = braceIdx + "{llc}".length;
    } else {
      pos = idx + 1;
    }
  }
  return text;
}

export function stripTcbox(text) {
  let pos = 0;
  while (true) {
    const idx = text.indexOf("\\tcbox", pos);
    if (idx === -1) {
      break;
    }
    let nextCharIdx = idx + "\\tcbox".length;
    while (nextCharIdx < text.length && /\s/.test(text[nextCharIdx])) {
      nextCharIdx++;
    }
    if (nextCharIdx < text.length && text[nextCharIdx] === "[") {
      const bracketIdx = text.indexOf("]", nextCharIdx);
      if (bracketIdx === -1) {
        pos = idx + 1;
        continue;
      }
      nextCharIdx = bracketIdx + 1;
    }
    while (nextCharIdx < text.length && /\s/.test(text[nextCharIdx])) {
      nextCharIdx++;
    }
    if (nextCharIdx < text.length && text[nextCharIdx] === "{") {
      let depth = 1;
      let i = nextCharIdx + 1;
      while (i < text.length && depth > 0) {
        if (text[i] === "{") {
          depth++;
        } else if (text[i] === "}") {
          depth--;
        }
        i++;
      }
      if (depth === 0) {
        const content = text.substring(nextCharIdx + 1, i - 1);
        text = text.substring(0, idx) + content + text.substring(i);
        pos = idx + content.length;
      } else {
        pos = idx + 1;
      }
    } else {
      pos = idx + 1;
    }
  }
  return text;
}

export function correctImagePaths(text) {
  return text.replace(/src=(["\']?)Images\//g, 'src=$1./Images/');
}

export function removeEmptyTableRows(text) {
  return text.replace(/^[ \t]*\|[ \t|]*(?:\r?\n|$)/gm, '');
}

export function splitSections(content) {
  const lines = content.split(/\r?\n/);
  const parts = [];
  let currentPart = [];
  let inCodeBlock = false;
  
  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      currentPart.push(line);
    } else if (!inCodeBlock && line.startsWith("# ")) {
      if (currentPart.length > 0) {
        parts.push(currentPart.join("\n"));
      }
      parts.push(line);
      currentPart = [];
    } else {
      currentPart.push(line);
    }
  }
  if (currentPart.length > 0) {
    parts.push(currentPart.join("\n"));
  }
  
  const sections = {};
  let currentHeader = null;
  const introContent = [];
  
  for (const part of parts) {
    const partStripped = part.trim();
    if (partStripped.startsWith("# ")) {
      currentHeader = partStripped;
    } else {
      if (currentHeader === null) {
        introContent.push(part);
      } else {
        sections[currentHeader] = (sections[currentHeader] || "") + part + "\n";
      }
    }
  }
  
  return { introContent: introContent.join("\n").trim(), sections };
}

// Determine if run directly
const isMain = process.argv[1] && (
  process.argv[1] === fileURLToPath(import.meta.url) ||
  process.argv[1].endsWith('converter.js')
);

if (isMain) {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const texFile = path.resolve(scriptDir, '../../../doc/ddl/ddl_reference.tex');
  const mdFile = path.resolve(scriptDir, '../../../doc/ddl/ddl_reference.md');
  const outDir = path.resolve(scriptDir, '../');
  
  console.log("Preprocessing LaTeX file...");
  try {
    let content = fs.readFileSync(texFile, 'utf8');
    content = simplifyLongtables(content);
    content = stripTcbox(content);
    content = content.replace(/\\centering/g, '');
    
    const tempTex = path.resolve(scriptDir, 'temp_ddl_ref.tex');
    fs.writeFileSync(tempTex, content, 'utf8');
    
    console.log("Running pandoc...");
    execSync(`pandoc "${tempTex}" -t gfm -o "${mdFile}" --wrap=none`);
    console.log("Successfully converted preprocessed LaTeX to MD");
    
    if (fs.existsSync(tempTex)) {
      fs.unlinkSync(tempTex);
    }
  } catch (err) {
    console.error("Could not run pandoc or preprocess:", err);
  }
  
  if (!fs.existsSync(mdFile)) {
    console.error("Error: markdown file not found.");
    process.exit(1);
  }
  
  let mdContent = fs.readFileSync(mdFile, 'utf8');
  mdContent = correctImagePaths(mdContent);
  mdContent = removeEmptyTableRows(mdContent);
  
  const { introContent, sections } = splitSections(mdContent);
  
  const mapping = {
    "intro": "index.md",
    "general": "general.md",
    "build": "build.md",
    "inputs": "inputs.md",
    "params": "params.md",
    "run": "run.md",
    "archive": "archive.md",
    "results": "results.md"
  };
  
  if (introContent) {
    const indexPath = path.join(outDir, "index.md");
    fs.writeFileSync(indexPath, introContent + "\n", 'utf8');
    console.log(`Wrote intro to ${indexPath}`);
  }
  
  for (const [header, body] of Object.entries(sections)) {
    const headerLower = header.toLowerCase();
    let matched = false;
    for (const [key, filename] of Object.entries(mapping)) {
      if (headerLower.includes(key)) {
        const destPath = path.join(outDir, filename);
        fs.writeFileSync(destPath, header + "\n" + body.trim() + "\n", 'utf8');
        console.log(`Wrote section '${header}' to ${destPath}`);
        matched = true;
        break;
      }
    }
    if (!matched) {
      console.warn(`Warning: section '${header}' not mapped to any file.`);
    }
  }
}
