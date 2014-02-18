import sublime_plugin
import sublime
import subprocess
import re

OCPKEY = "OCaml Autocompletion"
DEFAULT_INCLUDE = True

localInclude = DEFAULT_INCLUDE


class SublimeOCPIndex():
    local_cache = dict()

    def run_ocp(self, command, includes, opens, query, length, buildDir):
        args = ['ocp-index', command]

        if localInclude:
            for include in includes:
                args.append('-I')
                args.append(include)

        if buildDir is not None:
            args.append('--build')
            args.append(buildDir)

        for open in opens:
            args.append('-O')
            args.append(open)

        args.append(query)

        print(args)

        proc = subprocess.Popen(args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

        error  = proc.stderr.read().decode('utf-8').strip()
        output = proc.stdout.read().decode('utf-8').strip()

        if error:
            return error
        else:
            return output

    def extract_query(self, view, location):
        scopes = set(view.scope_name(location).split(" "))

        if len(set(["source.ocaml", "source.ocamllex", "source.ocamlyacc"]) & scopes) == 0:
            return None

        line = view.substr(sublime.Region(view.line(location).begin(), location))
        match = re.search(r"[,\s]*([A-Z][\w_.#']*|[\w_]+)$", line)

        if match != None:
            (context,) = match.groups()
            length = 0# len(context) - len(prefix)

            header = view.substr(sublime.Region(0, 4096))
            opens  = re.findall(r"^open ([\w.]+)$", header, flags=re.MULTILINE)

            if view.file_name() != None:
                (module,) = re.search(r"(\w+)\.ml.*$", view.file_name()).groups()
                opens.append(module.capitalize())


            buildDir = view.settings().get('ocamlbuild_dir')

            return (opens, context, length, buildDir)
        else:
            return None

    def query_type(self, view, location):
        endword = view.word(location).end()
        query = self.extract_query(view, endword)

        if query is not None:
            (opens, context, length, buildDir) = query

            return self.run_ocp('type', view.window().folders(), opens, context, length, buildDir)

    def query_completions(self, view, prefix, location):
        query = self.extract_query(view, location)

        if query is not None:
            (opens, context, length, buildDir) = query

            output = self.run_ocp('complete', view.window().folders(), opens, context, length, buildDir)


            results = []

            if prefix == "_":
                results.append(('_', '_'))

            variants = re.sub(r"\n\s+", " ", output).split("\n")

            for variant in variants:
                if variant.count(" ") > 0:
                    (replacement, rest) = str.split(variant, " ", 1)
                    actual_replacement = replacement[length:]
                    results.append((replacement + "\t" + rest, actual_replacement))

            if view.buffer_id() in self.local_cache:
                results += self.local_cache[view.buffer_id()]

            return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

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



## Boilerplate and connecting plugin classes to the real logic
sublimeocp = SublimeOCPIndex()

class SublimeOCPEventListener(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if len(locations) != 1:
            return

        return sublimeocp.query_completions(view, prefix, locations[0])

    if int(sublime.version()) < 3014:
        def on_close(self, view):
            sublimeocp.local_cache.pop(view.buffer_id())

        def on_load(self, view):
            sublimeocp.extract_locals(view)

        def on_post_save(self, view):
            sublimeocp.extract_locals(view)

        def on_selection_modified(self, view):
            view.erase_status(OCPKEY)

    else:
        def on_close_async(self, view):
            sublimeocp.local_cache.pop(view.buffer_id())

        def on_load_async(self, view):
            sublimeocp.extract_locals(view)

        def on_post_save_async(self, view):
            sublimeocp.extract_locals(view)

        def on_selection_modified_async(self, view):
            view.erase_status(OCPKEY)

class SublimeOcpTypes(sublime_plugin.TextCommand):
        def run(self, enable):
            locations = self.view.sel()

            result = sublimeocp.query_type(self.view, locations[0])

            if (result is None or len(result) == 0):
                displayType = "Unknown type"
            else:
                displayType = result

            self.view.set_status(OCPKEY,"Type: " + displayType)

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
    s.clear_on_change(OCPKEY)
    s.add_on_change(OCPKEY, read_pref)

# ST2 backwards compatibility
if (int(sublime.version()) < 3000):
    plugin_loaded()