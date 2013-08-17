import sublime_plugin
import sublime
import subprocess
import re

class SublimeOCPIndex(sublime_plugin.EventListener):

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

            header = view.substr(sublime.Region(0, 4096))
            opens  = re.findall(r"^open ([\w.]+)$", header, flags=re.MULTILINE)

            if view.file_name() != None:
                (module,) = re.search(r"(\w+)\.ml.*$", view.file_name()).groups()
                opens.append(module.capitalize())

            results = self.run_completion(view.window().folders(), opens, context, length)

            local_idents = []
            view.find_all(r"let(\s+rec)?\s+([\w']+)", 0, r"\2", local_idents)
            for local in local_idents:
                results.append((local + " : let", local))

            return results

    def run_completion(self, includes, opens, query, length):
        args = ['ocp-index', 'complete']

        for include in includes:
            args.append('-I')
            args.append(include)

        for open in opens:
            args.append('-O')
            args.append(open)

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
