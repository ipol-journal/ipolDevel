{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = (import nixpkgs) {
      inherit system;
    };
    python = "python310";

    python-env = pkgs."${python}".withPackages (p:
      with p; [
        cherrypy
        imageio
        numpy
        opencv4
        pillow
        python-magic
        requests
        tifffile
        cryptography
        urllib3
        result
        pytest
        ffmpeg-python
        fastapi
        pydantic
        uvicorn

        django
        gunicorn
      ]);
  in {
    packages.${system} = {
      core = pkgs.writeShellApplication {
        name = "ipol-core";
        runtimeInputs = [python-env];
        text = ''
          python ${self}/ipol_demo/modules/core/main.py "$@"
        '';
      };

      blobs = pkgs.writeShellApplication {
        name = "ipol-blobs";
        runtimeInputs = [python-env];
        text = ''
          uvicorn blobs:app --app-dir "${self}/ipol_demo/modules/blobs/" "$@"
        '';
      };

      archive = pkgs.writeShellApplication {
        name = "ipol-archive";
        runtimeInputs = [python-env];
        text = ''
          uvicorn archive:app --app-dir "${self}/ipol_demo/modules/archive/" "$@"
        '';
      };

      cp2 = pkgs.writeShellApplication {
        name = "ipol-cp2";
        runtimeInputs = [python-env];
        text = ''
          python ${self}/cp2/ControlPanel/manage.py "$@"
        '';
      };
    };
  };
}
