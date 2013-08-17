# OCaml autocompletion for Sublime Text

## Installation

    opam install ocp-index

## Configuration

You need to pass the `-bin-annot` flag to ocamlc/ocamlopt. You are probably using a build system, so follow the guide below.

### ocamlbuild

Ocamlbuild currently does not support generating binary annotations out of the box, but this can be solved by adding one line to `myocamlbuild.ml`:

    flag ["ocaml"; "compile"; "bin_annot"] (A"-bin-annot");

and `_tags`:

    true: bin_annot

## License

The MIT License
