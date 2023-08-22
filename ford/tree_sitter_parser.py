from ford.sourceform import (
    FortranBase,
    FortranContainer,
    FortranModule,
    FortranSubmodule,
    FortranFunction,
    FortranSubroutine,
    FortranProgram,
    FortranVariable,
    FortranType,
    FortranNamelist,
    remove_prefixes,
    _can_have_contains,
)
from typing import List, Optional

try:
    import tree_sitter_languages
    from tree_sitter import Node, Language

    FREE_FORM_LANGUAGE = tree_sitter_languages.get_language("fortran")
    FIXED_FORM_LANGUAGE = tree_sitter_languages.get_language("fixed_form_fortran")

    FREE_FORM_PARSER = tree_sitter_languages.get_parser("fortran")
    FIXED_FORM_PARSER = tree_sitter_languages.get_parser("fixed_form_fortran")

    tree_sitter_parser_available = True
except ImportError:
    tree_sitter_parser_available = False


def is_predoc_comment(comment: str, predocmark: str, predocmar_alt: str) -> bool:
    return is_doc_comment(comment, predocmark, predocmar_alt)


def is_doc_comment(comment: str, docmark: str, docmark_alt: str) -> bool:
    return comment.startswith(docmark) or comment.startswith(docmark_alt)


def decode(node: Node) -> str:
    return node.text.decode()


def maybe_decode(node: Optional[Node]) -> Optional[str]:
    return decode(node) if node else None


class Query:
    def __init__(self, language: Language, query: str):
        self.query = language.query(query)

    def __call__(self, node: Node) -> List[Node]:
        return [capture for capture, _ in self.query.captures(node)]

    def maybe_first(self, node: Node) -> Optional[Node]:
        if capture := self(node):
            return capture[0]
        return None

    def first(self, node: Node) -> Node:
        capture = self.maybe_first(node)
        if capture is None:
            raise ValueError("something's gone wrong")

        return capture


class TreeSitterParser:
    def __init__(self, free_form: bool = True, encoding: str = "utf-8"):
        self.encoding = encoding

        self.language = FREE_FORM_LANGUAGE if free_form else FIXED_FORM_LANGUAGE
        self.parser = FREE_FORM_PARSER if free_form else FIXED_FORM_PARSER

        self.program_query = Query(self.language, "(program) @program.def")
        self.module_query = Query(self.language, "(module) @module.def")
        self.submodule_query = Query(self.language, "(submodule) @submodule.def")
        self.submodule_parent_query = Query(
            self.language,
            """(submodule_statement
               ancestor: (module_name (name) @submodule.ancestor)?
               parent: (module_name (name) @submodule.parent)
               (name) @submodule.name
            )""",
        )

        self.contains_query = Query(self.language, "(internal_procedures) @contains")

        self.function_query = Query(self.language, "(function) @function.def")
        self.function_result_query = Query(
            self.language, "(function_result (identifier) @function.result)"
        )
        self.function_result_type_query = Query(
            self.language,
            "(function_statement [(intrinsic_type) (derived_type)] @function.result.type)",
        )
        self.function_attributes_query = Query(
            self.language, "(function_statement (procedure_qualifier) @function.attrs)"
        )

        self.subroutine_query = Query(self.language, "(subroutine) @subroutine.def")

        self.procedure_parameters_query = Query(
            self.language, "(parameters) @function.arg"
        )

        self.language_binding_query = Query(
            self.language, "(language_binding) @function.bind"
        )

        self.name_query = Query(self.language, "(name) @name")

        self.namelist_query = Query(
            self.language, "(namelist_statement (variable_group) @namelist.def)"
        )
        self.namelist_variables_query = Query(
            self.language, "(variable_group (identifier) @var)"
        )

    def _get_name(self, node):
        name_capture = self.name_query(node)[0]
        return name_capture.text.decode(self.encoding)

    @staticmethod
    def read_docstring(node: Node, docmark: str) -> List[str]:
        comments = []

        prev_sibling = node if node.prev_sibling else node.parent
        while prev_sibling := prev_sibling.prev_sibling:
            if prev_sibling.type != "comment":
                break
            comment = prev_sibling.text.decode()
            if is_predoc_comment(comment, "!>", "!*"):
                comments.append(remove_prefixes(comment, "!>", "!*"))

        next_sibling = node
        while next_sibling := next_sibling.next_sibling:
            if next_sibling.type != "comment":
                break
            comment = next_sibling.text.decode()
            if is_doc_comment(comment, "!!", "!<"):
                comments.append(remove_prefixes(comment, "!!", "!<"))

        return comments

    def parse_source(self, entity: FortranContainer, source: Node):
        if hasattr(entity, "modules"):
            for module in self.module_query(source):
                entity.modules.append(self.parse_module(entity, module))

        if hasattr(entity, "submodules"):
            for module in self.submodule_query(source):
                entity.submodules.append(self.parse_submodule(entity, module))

        if hasattr(entity, "programs"):
            for program in self.program_query(source):
                entity.programs.append(self.parse_program(entity, program))

        # attributes

        # block data

        # associate

        # namelists
        if hasattr(entity, "namelists"):
            for namelist in self.namelist_query(source):
                # Don't find namelists in children
                if namelist.parent.parent != source:
                    continue
                entity.namelists.append(self.parse_namelist(entity, namelist))

        # derived type

        # interface

        # boundproc

        # finalproc

        # enum

        # common

        # variable

        # use

        # calls

        if not isinstance(entity, _can_have_contains):
            return

        if not (contains := self.contains_query.maybe_first(source)):
            return

        if isinstance(entity, FortranType):
            self.parse_derived_type(entity, source)
            return

        for function in self.function_query(contains):
            if function.parent.parent != source:
                continue
            entity.functions.append(self.parse_function(entity, function))

        for subroutine in self.subroutine_query(contains):
            entity.subroutines.append(self.parse_subroutine(entity, subroutine))

    def parse_program(self, parent: FortranContainer, program: Node) -> FortranProgram:
        return FortranProgram(self, program, name=self._get_name(program))

    def parse_module(self, parent: FortranContainer, module: Node) -> FortranModule:
        return FortranModule(
            self,
            module,
            parent=parent,
            name=self._get_name(module),
        )

    def parse_submodule(
        self, parent: FortranContainer, submodule: Node
    ) -> FortranSubmodule:
        name = self._get_name(submodule)
        return FortranSubmodule(self, submodule, name=name)

    def parse_attributes(self, parent, attributes):
        pass

    def parse_block_data(self, parent, node):
        pass

    def parse_associate(self, parent, node):
        pass

    def parse_subroutine(self, parent, node):
        attributes = self.function_attributes_query(node)
        arguments = self.procedure_parameters_query.first(node)
        bind = self.language_binding_query.maybe_first(node)

        subroutine = FortranSubroutine(
            self,
            node,
            parent=parent,
            name=self._get_name(node),
            attributes="\n".join(decode(attr) for attr in attributes),
            arguments=decode(arguments),
            bindC=maybe_decode(bind),
        )
        subroutine._cleanup()
        return subroutine

    def parse_function(self, parent: FortranContainer, node: Node) -> FortranFunction:
        attributes = self.function_attributes_query(node)
        name = self._get_name(node)
        arguments = self.procedure_parameters_query.first(node)
        result = self.function_result_query.maybe_first(node)
        bind = self.language_binding_query.maybe_first(node)

        function = FortranFunction(
            self,
            node,
            parent=parent,
            name=name,
            attributes="\n".join(decode(attr) for attr in attributes),
            result=maybe_decode(result),
            arguments=decode(arguments),
            bindC=maybe_decode(bind),
        )

        if result_type := self.function_result_type_query.maybe_first(node):
            function.retvar = FortranVariable(
                name=function.retvar, parent=function, vartype=decode(result_type)
            )

        function._cleanup()
        return function

    def parse_namelist(self, parent, node):
        variables = [decode(var) for var in self.namelist_variables_query(node)]
        return FortranNamelist(
            node, self, parent=parent, name=self._get_name(node), vars=variables
        )

    def parse_derived_type(self, parent, node):
        pass

    def parse_interface(self, parent, node):
        pass

    def parse_bound_procedure(self, parent, node):
        pass

    def parse_final_procedure(self, parent, node):
        pass

    def parse_enum(self, parent, node):
        pass
