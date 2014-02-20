import sublime_plugin
import sublime
import subprocess
import re

OCPKEY = "OCaml Autocompletion"

class SublimeOCPIndex():
    local_cache = dict()

    def run_ocp(self, command, includes, module, query, length, context, settings):
        args = ['ocp-index', command]

        if context is not None:
            args.append('--context')
            args.append(context)

        viewInclude = settings.get('sublime_ocp_index_include_local_packages')
        if viewInclude is not None:
            allowInclude = viewInclude
        else:
            allowInclude = True

        if allowInclude:
            for include in includes:
                args.append('-I')
                args.append(include)

        buildDir = settings.get('sublime_ocp_index_build_dir')
        if buildDir is not None:
            args.append('--build')
            args.append(buildDir)

        if module is not None:
            args.append('-F')
            args.append(module)

        args.append(query)

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
        match = re.search(r"[,\s]*([A-Z][\w_.#']*|[\w_#']+)$", line)

        if match != None:
            (queryString,) = match.groups()
            length = 0# len(queryString) - len(prefix)

            header = view.substr(sublime.Region(0, 4096))
            module = None
            context = None

            if view.file_name() != None:
                (moduleName,) = re.search(r"(\w+)\.ml.*$", view.file_name()).groups()
                module = moduleName.capitalize()

                (line,col) = view.rowcol(location)
                context = "%s:%d,%d" % (view.file_name(), line, col)


            settings = view.settings()

            return (module, queryString, length, context, settings)
        else:
            return None

    def query_type(self, view, location):
        endword = view.word(location).end()
        while view.substr(endword) in ['_', '#', '\'']:
            endword = endword + 1
            if view.substr(endword) is not ' ':
                endword = view.word(endword).end()

        query = self.extract_query(view, endword)

        if query is not None:
            (module, queryString, length, context, settings) = query

            result = self.run_ocp('type', view.window().folders(), module, queryString, length, context, settings)

            if (result is None or len(result) == 0):
                return "Unknown type: '%s'" % queryString
            else:
                return "Type: %s" % result


    def query_completions(self, view, prefix, location):
        query = self.extract_query(view, location)

        if query is not None:
            (module, queryString, length, context, settings) = query

            output = self.run_ocp('complete', view.window().folders(), module, queryString, length, context, settings)


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

            if result is not None:
                self.view.set_status(OCPKEY, result)

# ST2 backwards compatibility
if (int(sublime.version()) < 3000):
    plugin_loaded()