# OCaml autocompletion for Sublime Text

## Installation

    opam install ocp-index

## OPAM Configuration

This plugin uses `ocp-index -I <folder>` to enable searching local project libraries. If instead you are using libraries in OPAM, the use of `-I` disables the default ocp-index behaviour to search for and use the OPAM main directory. To switch to showing OPAM libraries in autocomplete results, add the following to your sublime preferences:

    "autocomplete-local-ocaml-packages": false

## Build configuration

You need to pass the `-bin-annot` flag to ocamlc/ocamlopt. You are probably using a build system, so follow the guide below.

### ocamlbuild

Ocamlbuild 4.01 supports generating binary annotations out of the box, with the bin_annot tag. In your `_tags`:

    true: bin_annot

For earlier versions of Ocamlbuild, this can be replicated by adding one line to `myocamlbuild.ml`:

    flag ["ocaml"; "compile"; "bin_annot"] (A"-bin-annot");


## License

The MIT License
