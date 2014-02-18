import sublime_plugin
import sublime
import subprocess
import re

DEFAULT_INCLUDE = True

localInclude = DEFAULT_INCLUDE

def plugin_loaded():
    s = sublime.load_settings('Preferences.sublime-settings')

    def read_pref():
        include = s.get('autocomplete-local-ocaml-packages')
        global localInclude
        if include is not None:
            localInclude = include
        else:
            localInclude = DEFAULT_INCLUDE

    # read initial setting
    read_pref()
    # listen for changes
    s.clear_on_change("OCaml Autocompletion")
    s.add_on_change("OCaml Autocompletion", read_pref)

# ST2 backwards compatibility
if (int(sublime.version()) < 3000):
    plugin_loaded()

class SublimeOCPIndex(sublime_plugin.EventListener):

    local_cache = dict()

    def on_query_completions(self, view, prefix, locations):
        if len(locations) != 1:
            return

        (location,) = locations
        scopes      = set(view.scope_name(location).split(" "))

        if len(set(["source.ocaml", "source.ocamllex", "source.ocamlyacc"]) & scopes) == 0:
            return

        line = view.substr(sublime.Region(view.line(locations[0]).begin(), locations[0]))
        match = re.search(r"[,\s]*([A-Z][\w_.']*|[\w_]+)$", line)

        if match != None:
            (context,) = match.groups()
            length = 0# len(context) - len(prefix)

            header = view.substr(sublime.Region(0, 4096))
            opens  = re.findall(r"^open ([\w.]+)$", header, flags=re.MULTILINE)

            if view.file_name() != None:
                (module,) = re.search(r"(\w+)\.ml.*$", view.file_name()).groups()
                opens.append(module.capitalize())

            results = []

            if prefix == "_":
                results.append(('_', '_'))

            results += self.run_completion(view.window().folders(), opens, context, length)

            if view.buffer_id() in self.local_cache:
                results += self.local_cache[view.buffer_id()]

            return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

    if int(sublime.version()) < 3014:
        def on_close(self, view):
            self.local_cache.pop(view.buffer_id())

        def on_load(self, view):
            self.extract_locals(view)

        def on_post_save(self, view):
            self.extract_locals(view)

    else:
        def on_close_async(self, view):
            self.local_cache.pop(view.buffer_id())

        def on_load_async(self, view):
            self.extract_locals(view)

        def on_post_save_async(self, view):
            self.extract_locals(view)

    def run_completion(self, includes, opens, query, length):
        args = ['ocp-index', 'complete']

        if localInclude:
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

        output   = proc.stdout.read().decode('utf-8').strip()
        variants = re.sub(r"\n\s+", " ", output).split("\n")

        result = []

        for variant in variants:
            if variant.count(" ") > 0:
                (replacement, rest) = str.split(variant, " ", 1)
                actual_replacement = replacement[length:]
                result.append((replacement + "\t" + rest, actual_replacement))

        return result

    def extract_locals(self, view):
        local_defs = []
        view.find_all(r"let(\s+rec)?\s+(([?~]?[\w']+\s*)+)=", 0, r"\2", local_defs)
        view.find_all(r"fun\s+(([?~]?[\w']+\s*)+)->", 0, r"\1", local_defs)

        locals = set()
        for definition in local_defs:
            for local in str.split(definition):
                (local,) = re.match(r"^[?~]?(.+)", local).groups()
                locals.add((local + "\tlet", local))

        self.local_cache[view.buffer_id()] = list(locals)
