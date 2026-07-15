import { describe, it, expect } from 'vitest';
import { simplifyLongtables, stripTcbox, correctImagePaths, splitSections, removeEmptyTableRows } from './converter.js';

describe('simplifyLongtables', () => {
  it('simplifies single-line longtable column spec', () => {
    const input = '\\begin{longtable}{|>{\\bf}L{\\dimexpr 0.28\\linewidth}|L{\\dimexpr 0.57\\linewidth}|c|}';
    expect(simplifyLongtables(input)).toBe('\\begin{longtable}{llc}');
  });

  it('simplifies multi-line longtable column spec with nested braces', () => {
    const input = `\\begin{longtable}{|>{\\bf}L{\\dimexpr 
0.28\\linewidth}|L{\\dimexpr 
0.57\\linewidth}|c|}`;
    expect(simplifyLongtables(input)).toBe('\\begin{longtable}{llc}');
  });

  it('does not touch text outside of column spec', () => {
    const input = 'some text \\begin{longtable}{|c|} other text';
    expect(simplifyLongtables(input)).toBe('some text \\begin{longtable}{llc} other text');
  });
});

describe('stripTcbox', () => {
  it('removes simple tcbox wrapper', () => {
    const input = '\\tcbox{my content}';
    expect(stripTcbox(input)).toBe('my content');
  });

  it('removes tcbox with options block', () => {
    const input = '\\tcbox[sharp corners, boxsep=0.0mm]{my content}';
    expect(stripTcbox(input)).toBe('my content');
  });

  it('handles spaces between tcbox, brackets, and braces', () => {
    const input = '\\tcbox [options]  {my content}';
    expect(stripTcbox(input)).toBe('my content');
  });

  it('handles nested braces inside content', () => {
    const input = '\\tcbox{\\includegraphics{Images/test.png}}';
    expect(stripTcbox(input)).toBe('\\includegraphics{Images/test.png}');
  });
});

describe('correctImagePaths', () => {
  it('corrects src with double quotes', () => {
    const input = '<img src="Images/geojson_example.png" />';
    expect(correctImagePaths(input)).toBe('<img src="./Images/geojson_example.png" />');
  });

  it('corrects src with single quotes', () => {
    const input = '<img src=\'Images/geojson_example.png\' />';
    expect(correctImagePaths(input)).toBe('<img src=\'./Images/geojson_example.png\' />');
  });

  it('corrects src without quotes', () => {
    const input = '<img src=Images/geojson_example.png />';
    expect(correctImagePaths(input)).toBe('<img src=./Images/geojson_example.png />');
  });

  it('corrects multiple src in one text', () => {
    const input = 'src="Images/one.png" and src=\'Images/two.png\'';
    expect(correctImagePaths(input)).toBe('src="./Images/one.png" and src=\'./Images/two.png\'');
  });
});

describe('removeEmptyTableRows', () => {
  it('removes empty row at the bottom of a markdown table', () => {
    const input = `| key | description |
|:---|:---|
| type | range |
|  |  |

Some text`;
    const expected = `| key | description |
|:---|:---|
| type | range |

Some text`;
    expect(removeEmptyTableRows(input)).toBe(expected);
  });

  it('handles empty rows with different spacing and pipe counts', () => {
    const input = `| col1 | col2 | col3 |
|---|---|---|
| val1 | val2 | val3 |
|   |   |   |
| val4 | val5 | val6 |`;
    const expected = `| col1 | col2 | col3 |
|---|---|---|
| val1 | val2 | val3 |
| val4 | val5 | val6 |`;
    expect(removeEmptyTableRows(input)).toBe(expected);
  });
});

describe('splitSections', () => {
  it('splits sections by level 1 header', () => {
    const content = `Some intro text

# The *general* section
general content

# The *build* section
build content`;
    const { introContent, sections } = splitSections(content);
    expect(introContent).toBe('Some intro text');
    expect(sections['# The *general* section'].trim()).toBe('general content');
    expect(sections['# The *build* section'].trim()).toBe('build content');
  });

  it('ignores headers inside fenced code blocks', () => {
    const content = `Some intro text

# The *inputs* section
Inputs content here

\`\`\` python
# -*- coding: UTF-8 -*-
# Load GeoJSON
print("hello")
\`\`\`

More inputs content`;
    const { sections } = splitSections(content);
    expect(sections['# The *inputs* section']).toContain('# -*- coding: UTF-8 -*-');
    expect(sections['# The *inputs* section']).toContain('# Load GeoJSON');
    expect(Object.keys(sections)).toHaveLength(1);
  });
});
