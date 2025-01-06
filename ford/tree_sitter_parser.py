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

from tree_sitter import Node, Language, TreeCursor, Parser
import tree_sitter_fortran

FREE_FORM_LANGUAGE = Language(tree_sitter_fortran.language())
# FIXME: use correct language when fixed form is on PyPI
FIXED_FORM_LANGUAGE = Language(tree_sitter_fortran.language())

FREE_FORM_PARSER = Parser(FREE_FORM_LANGUAGE)
FIXED_FORM_PARSER = Parser(FREE_FORM_LANGUAGE)


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
        # This is pretty crude, just collecting all the captures
        captures = []
        for capture in self.query.captures(node).values():
            captures.extend(capture)
        return captures

    def maybe_first(self, node: Node) -> Optional[Node]:
        if capture := self(node):
            return capture[0]
        return None

    def first(self, node: Node) -> Node:
        capture = self.maybe_first(node)
        if capture is None:
            raise ValueError("something's gone wrong")

        return capture


@contextmanager
def descend_one_node(cursor: TreeCursor) -> TreeCursor:
    cursor.goto_first_child()
    try:
        yield cursor
    finally:
        cursor.goto_parent()


class TreeSitterParser:
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

        self._parse_node(entity, cursor)
        while cursor.goto_next_sibling():
            self._parse_node(entity, cursor)

    def _parse_node(self, entity: FortranContainer, cursor: TreeCursor):
        if cursor.node.type == "program":
            if not hasattr(entity, "programs"):
                self.warn_invalid_node(entity, "programs")
                return

            with descend_one_node(cursor) as cursor:
                entity.programs.append(self.parse_program(entity, cursor))

        elif cursor.node.type == "module":
            if not hasattr(entity, "modules"):
                self.warn_invalid_node(entity, "modules")
                return

            with descend_one_node(cursor) as cursor:
                entity.modules.append(self.parse_module(entity, cursor))

        elif cursor.node.type == "submodule":
            if not hasattr(entity, "submodules"):
                self.warn_invalid_node(entity, "submodules")
                return

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
                return

            with descend_one_node(cursor) as cursor:
                entity.functions.append(self.parse_function(entity, cursor))

        elif cursor.node.type == "subroutine":
            if not hasattr(entity, "subroutines"):
                self.warn_invalid_node(entity, "subroutines")
                return

            with descend_one_node(cursor) as cursor:
                entity.subroutines.append(self.parse_subroutine(entity, cursor))

        elif cursor.node.type == "variable_declaration":
            if not hasattr(entity, "variables"):
                self.warn_invalid_node(entity, "variables")
                return

            with descend_one_node(cursor):
                entity.variables.extend(self.parse_variable(entity, cursor))

        elif cursor.node.type == "namelist_statement":
            if not hasattr(entity, "namelists"):
                self.warn_invalid_node(entity, "namelists")
                return

            with descend_one_node(cursor):
                entity.namelists.extend(self.parse_namelist(entity, cursor))



        # attributes

        # block data

        # associate

        # derived type

        # interface

        # boundproc

        # finalproc

        # enum

        # common

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
        return FortranProgram(self, program, parent, name=self._get_name(program))

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
        result_name = None
        result_type = None
        arguments = []
        bindC = None

        with descend_one_node(cursor):
            while True:
                if cursor.node.type == "procedure_qualifier":
                    attributes.append(decode(cursor.node))
                elif cursor.node.type in ("intrinsic_type", "derived_type"):
                    result_type = decode(cursor.node)
                elif cursor.node.type == "parameters":
                    arguments = [decode(arg) for arg in cursor.node.named_children]
                elif cursor.node.type == "function_result":
                    result_name = decode(cursor.node.named_children[0])
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
            result_name=result_name,
            result_type=result_type,
            arguments=arguments,
            bindC=bindC,
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
