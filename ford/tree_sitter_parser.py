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
from contextlib import contextmanager

try:
    import tree_sitter_languages
    from tree_sitter import Node, Language, TreeCursor

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


@contextmanager
def descend_one_node(cursor: TreeCursor) -> TreeCursor:
    cursor.goto_first_child()
    try:
        yield cursor
    finally:
        cursor.goto_parent()


class TreeSitterCursorParser:
    def __init__(self, free_form: bool = True, encoding: str = "utf-8"):
        self.encoding = encoding

        self.language = FREE_FORM_LANGUAGE if free_form else FIXED_FORM_LANGUAGE
        self.parser = FREE_FORM_PARSER if free_form else FIXED_FORM_PARSER

        self.name_query = Query(self.language, "(name) @name")

    def _get_name(self, node: TreeCursor):
        name_capture = self.name_query(node.node)[0]
        return name_capture.text.decode(self.encoding)

    @staticmethod
    def read_docstring(cursor: TreeCursor, docmark: str) -> List[str]:
        comments = []

        node = cursor.node

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

    def warn_invalid_node(self, entity: FortranContainer, collection: str):
        print(f"{entity.obj} {entity.name!r} can't have {collection}")

    def parse_source(self, entity: FortranContainer, cursor: TreeCursor):
        if cursor.node.type == "translation_unit":
            cursor.goto_first_child()

        while cursor.goto_next_sibling():
            # print(cursor.node.type, cursor.node.start_point)
            if cursor.node.type == "program":
                if not hasattr(entity, "programs"):
                    self.warn_invalid_node(entity, "programs")
                    continue

                with descend_one_node(cursor) as cursor:
                    entity.programs.append(self.parse_program(entity, cursor))

            elif cursor.node.type == "module":
                if not hasattr(entity, "modules"):
                    self.warn_invalid_node(entity, "modules")
                    continue

                with descend_one_node(cursor) as cursor:
                    entity.modules.append(self.parse_module(entity, cursor))

            elif cursor.node.type == "submodule":
                if not hasattr(entity, "submodules"):
                    self.warn_invalid_node(entity, "submodules")
                    continue

                with descend_one_node(cursor) as cursor:
                    entity.submodules.append(self.parse_submodule(entity, cursor))

            elif cursor.node.type == "internal_procedures":
                if not isinstance(entity, _can_have_contains):
                    print(f"{entity.obj} {entity.name!r} can't have functions and that")

                with descend_one_node(cursor) as cursor:
                    self.parse_source(entity, cursor)

            elif cursor.node.type == "function":
                if not hasattr(entity, "functions"):
                    self.warn_invalid_node(entity, "functions")
                    continue

                with descend_one_node(cursor) as cursor:
                    entity.functions.append(self.parse_function(entity, cursor))

            elif cursor.node.type == "subroutine":
                if not hasattr(entity, "subroutines"):
                    self.warn_invalid_node(entity, "subroutines")
                    continue

                with descend_one_node(cursor) as cursor:
                    entity.subroutines.append(self.parse_subroutine(entity, cursor))

            elif cursor.node.type == "variable_declaration":
                if not hasattr(entity, "variables"):
                    self.warn_invalid_node(entity, "variables")
                    continue

                with descend_one_node(cursor):
                    entity.variables.extend(self.parse_variable(entity, cursor))

            elif cursor.node.type == "namelist_statement":
                if not hasattr(entity, "namelists"):
                    self.warn_invalid_node(entity, "namelists")
                    continue

                with descend_one_node(cursor):
                    entity.namelists.extend(self.parse_namelist(entity, cursor))

        # attributes

        # block data

        # associate

        # namelists

        # derived type

        # interface

        # boundproc

        # finalproc

        # enum

        # common

        # variable

        # use

        # calls

        # if not isinstance(entity, _can_have_contains):
        #     return

        # if not (contains := self.contains_query.maybe_first(cursor)):
        #     return

        # if isinstance(entity, FortranType):
        #     self.parse_derived_type(entity, cursor)
        #     return

    def parse_program(
        self, parent: FortranContainer, program: TreeCursor
    ) -> FortranProgram:
        return FortranProgram(self, program, name=self._get_name(program))

    def parse_module(
        self, parent: FortranContainer, module: TreeCursor
    ) -> FortranModule:
        return FortranModule(
            self,
            module,
            parent=parent,
            name=self._get_name(module),
        )

    def parse_submodule(
        self, parent: FortranContainer, submodule: TreeCursor
    ) -> FortranSubmodule:
        return FortranSubmodule(self, submodule, name=self._get_name(submodule))

    def parse_attributes(self, parent, attributes):
        pass

    def parse_block_data(self, parent, node):
        pass

    def parse_associate(self, parent, node):
        pass

    def parse_subroutine(self, parent, node):
        # attributes = self.function_attributes_query(node)
        # arguments = self.procedure_parameters_query.first(node)
        # bind = self.language_binding_query.maybe_first(node)

        subroutine = FortranSubroutine(
            self,
            node,
            parent=parent,
            name=self._get_name(node),
            attributes=[],
            arguments=[],
            bindC=None,
        )
        subroutine._cleanup()
        return subroutine

    def parse_function(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> FortranFunction:
        attributes = []
        result = None
        result_type = None
        arguments = ""
        bindC = None

        with descend_one_node(cursor):
            while True:
                if cursor.node.type == "procedure_qualifier":
                    attributes.append(decode(cursor.node))
                elif cursor.node.type in ("intrinsic_type", "derived_type"):
                    result_type = decode(cursor.node)
                elif cursor.node.type == "parameters":
                    arguments = decode(cursor.node)
                elif cursor.node.type == "function_result":
                    result = decode(cursor.node.named_children[0])
                elif cursor.node.type == "language_binding":
                    bindC = decode(cursor.node)

                if not cursor.goto_next_sibling():
                    break

        function = FortranFunction(
            self,
            cursor,
            parent=parent,
            name=self._get_name(cursor),
            attributes=",".join(attributes),
            result=result,
            arguments=arguments,
            bindC=bindC,
        )

        if result_type is not None:
            function.retvar = FortranVariable(
                name=function.retvar, parent=function, vartype=result_type
            )

        function._cleanup()
        return function

    def parse_variable(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> List[FortranVariable]:
        attributes = []
        vartype = None
        names = []

        while True:
            if cursor.node.type in ["intrinsic_type", "derived_type"]:
                vartype = decode(cursor.node)
            elif cursor.node.type == "type_qualifier":
                attributes.append(decode(cursor.node))
            elif cursor.node.type == "identifier":
                names.append(decode(cursor.node))

            if not cursor.goto_next_sibling():
                break

        return [
            FortranVariable(
                name=name, parent=parent, vartype=vartype, attribs=attributes
            )
            for name in names
        ]

    def parse_namelist(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> List[FortranNamelist]:
        namelists = []

        while cursor.goto_next_sibling():
            if cursor.node.type != "variable_group":
                continue
            with descend_one_node(cursor):
                name = None
                variables = []
                while True:
                    if cursor.node.type == "name":
                        name = decode(cursor.node)
                    elif cursor.node.type == "identifier":
                        variables.append(decode(cursor.node))
                    if not cursor.goto_next_sibling():
                        break
                namelists.append(
                    FortranNamelist(
                        cursor, self, parent=parent, name=name, vars=variables
                    )
                )

        return namelists

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
