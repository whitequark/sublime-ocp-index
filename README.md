# OCaml autocompletion for Sublime Text

## Installation

    opam install ocp-index

## Usage

Within OCaml syntax files:

- Standard sublime autocompletion is completely replaced with OCaml autocompletion
- Type inspection of variables is available via the `alt+a` shortcut, which displays the type in the status bar

## Build configuration

You need to pass the `-bin-annot` flag to ocamlc/ocamlopt. You are probably using a build system, so follow the guide below.

If you are not using one of the [standard build output folders](https://github.com/OCamlPro/ocp-index/blob/81ad7ac148bab1188bcf401f8cdd3859730f5aa8/src/indexMisc.ml#L102) then a setting is available to pass the `--build` parameter to `ocp-index`:

    "sublime_ocp_index_build_dir": "gen/ml"

This setting can be applied as a user preference or (recommended) in your `.sublime-project` file.

### ocamlbuild

Ocamlbuild 4.01 supports generating binary annotations out of the box, with the bin_annot tag. In your `_tags`:

    true: bin_annot

For earlier versions of Ocamlbuild, this can be replicated by adding one line to `myocamlbuild.ml`:

    flag ["ocaml"; "compile"; "bin_annot"] (A"-bin-annot");


## License

The MIT License

## A note about ocp-index versions

This plugin uses `ocp-index -I <folder>` to enable searching local project libraries. Prior to the 1.0.2 release, this disabled searching OPAM libraries. To show OPAM libraries in autocomplete results with this version, use the following setting:

    "sublime_ocp_index_include_local_packages": false

This can be applied globally in your user settings or overridden in a `.sublime-project` file.