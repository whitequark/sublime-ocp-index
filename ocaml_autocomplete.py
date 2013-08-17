import sublime_plugin
import sublime
import subprocess
import re

class OCamlAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if len(locations) != 1:
            return

        (location,) = locations

        if "source.ocaml" not in view.scope_name(location).split(" "):
            return

        line = view.substr(sublime.Region(view.line(locations[0]).begin(), locations[0]))
        match = re.search(r"[,\s]*([\w.]+)$", line)

        if match != None:
            (context,) = match.groups()
            length = len(context) - len(prefix)
            return self.run_completion(view.window().folders(), context, length)

    def run_completion(self, includes, query, length):
        args = ['ocp-index', 'complete']

        for include in includes:
            args.append('-I')
            args.append(include)

        args.append(query)

        proc = subprocess.Popen(args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

        output   = str(proc.stdout.read(), encoding='utf-8').strip()
        variants = re.sub(r"\n\s+", " ", output).split("\n")

        result = []

        for variant in variants:
            if variant.count(" ") > 0:
                (replacement, rest) = str.split(variant, " ", 1)
                actual_replacement = replacement[length:]
                result.append((replacement + " : " + rest, actual_replacement))

        return result
