{
  description = "bookie — Python development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = pkgs.python313.withPackages (ps:
        with ps; [
          fastapi
          uvicorn
          uvloop
          httptools
          websockets
          watchfiles
          python-dotenv

          sqlalchemy
          alembic
          asyncpg
          aiosqlite
          greenlet
          pydantic-settings

          pytest
          pytest-cov
          pytest-asyncio
          httpx
          ruff
          mypy
          ipython

          typer
          rich

          passlib
          bcrypt
          python-jose
          email-validator
          python-multipart
        ]);
    in {
      devShells.default = pkgs.mkShell {
        packages = [
          pythonEnv
          pkgs.pre-commit
          pkgs.git
          pkgs.just
          pkgs.ripgrep
          pkgs.fd
        ];

        shellHook = ''
          export PYTHONPATH="$PWD/src:$PYTHONPATH"

          echo

          if [ -f .pre-commit-config.yaml ]; then
            pre-commit install >/dev/null 2>&1 || true
          fi


          echo "Commands:"
          echo "  just test                    run tests"
          echo "  just cov                     coverage"
          echo "  just lint                    lint"
          echo "  just fmt                     format"
          echo "  just check                   type check"
          echo "  just run                     run the app"
          echo "  just migrate \"description\"   generate a migration"
          echo "  just upgrade                 apply migrations"
          echo "  just downgrade               roll back one step"
          echo "  just db-drop                 delete the local database"
          echo
          echo "CLI:"
          echo "  python cli.py --help               show all commands"
          echo "  python cli.py ping                 check the API is up"
          echo "  python cli.py bookmarks list       list bookmarks"
          echo
          exec zsh
        '';
      };
    });
}
