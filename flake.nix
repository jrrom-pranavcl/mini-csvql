{
  description = "devshell for csvql";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs = { self , nixpkgs ,... }:
    let
      system = "x86_64-linux";
    in
      {
        devShells."${system}".default = let
          pkgs = import nixpkgs { inherit system; };
        in pkgs.mkShell {
          packages = with pkgs; [
            (python3.withPackages
              (ps: with ps; [
                pyparsing
                black
              ])
            )
            basedpyright
            black
          ];
        };
      };

}

