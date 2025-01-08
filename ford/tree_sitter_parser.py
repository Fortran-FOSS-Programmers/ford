from ford.sourceform import (
    FortranBlockData,
    FortranContainer,
    FortranCodeUnit,
    FortranEnum,
    FortranInterface,
    FortranModule,
    FortranModuleProcedureImplementation,
    FortranSubmodule,
    FortranFunction,
    FortranSubroutine,
    FortranProgram,
    FortranVariable,
    FortranType,
    FortranNamelist,
    _can_have_contains,
    SPLIT_RE,
    ModuleUses,
    ModuleUsesItem,
)

from typing import List, Optional, Generator
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


def has_named_child(cursor: TreeCursor, name: str) -> bool:
    return any(child.type == name for child in cursor.node.named_children)


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


def traverse_children(cursor: TreeCursor) -> Generator[Node, None, None]:
    """Iterate a cursor over just its immediate children"""
    with descend_one_node(cursor):
        while True:
            yield cursor.node
            if not cursor.goto_next_sibling():
                break


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
        """Read either the preceeding or following comments if they
        start with the appropriate docmark.

        TODO: use appropriate docmark from settings

        TODO: read whole blocks that start with the docmark

        """
        comments = []

        node = cursor.node

        prev_sibling = node if node.prev_sibling else node.parent
        while prev_sibling := prev_sibling.prev_sibling:
            if prev_sibling.type != "comment":
                break
            comment = prev_sibling.text.decode()
            if is_predoc_comment(comment, "!>", "!*"):
                comments.append(comment[2:])

        next_sibling = node
        while next_sibling := next_sibling.next_sibling:
            if next_sibling.type != "comment":
                break
            comment = next_sibling.text.decode()
            if is_doc_comment(comment, "!!", "!<"):
                comments.append(comment[2:])

        return comments

    def warn_invalid_node(self, entity: FortranContainer, collection: str):
        print(f"{entity.obj} {entity.name!r} can't have {collection}")

    def parse_source(self, entity: FortranContainer, cursor: TreeCursor):
        if cursor.node.type == "translation_unit":
            cursor.goto_first_child()

        child_permission = (
            "public" if isinstance(entity, FortranType) else entity.permission
        )

        while True:
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

            elif cursor.node.type == "module_procedure":
                if not hasattr(entity, "modprocedures"):
                    self.warn_invalid_node(entity, "modprocedures")
                    return

                with descend_one_node(cursor) as cursor:
                    entity.modprocedures.append(
                        self.parse_module_procedure(entity, cursor)
                    )

            elif cursor.node.type == "interface":
                if not isinstance(entity, FortranCodeUnit):
                    self.warn_invalid_node(entity, "interfaces")

                with descend_one_node(cursor) as cursor:
                    self.parse_interface(entity, cursor)

            elif cursor.node.type in ("variable_declaration", "procedure_statement"):
                if not hasattr(entity, "variables"):
                    self.warn_invalid_node(entity, "variables")
                    return

                entity.variables.extend(
                    self.parse_variable(entity, cursor, child_permission)
                )

            elif cursor.node.type == "namelist_statement":
                if not hasattr(entity, "namelists"):
                    self.warn_invalid_node(entity, "namelists")
                    return

                with descend_one_node(cursor):
                    entity.namelists.extend(self.parse_namelist(entity, cursor))

            elif cursor.node.type == "derived_type_definition":
                if not hasattr(entity, "types"):
                    self.warn_invalid_node(entity, "types")
                    return

                with descend_one_node(cursor):
                    entity.types.append(self.parse_derived_type(entity, cursor))

            elif cursor.node.type == "use_statement":
                if not hasattr(entity, "uses"):
                    self.warn_invalid_node(entity, "uses")
                    return

                entity.uses.append(self.parse_use_statement(entity, cursor))

            elif cursor.node.type in ("public_statement", "private_statement"):
                if cursor.node.named_child_count == 0:
                    child_permission = decode(cursor.node.child(0)).lower()
                    if not isinstance(entity, FortranType):
                        entity.permission = child_permission
                else:
                    self.parse_attributes(entity, cursor)

            elif cursor.node.type == "variable_modification":
                self.parse_attributes(entity, cursor)

            # block data

            # associate

            # boundproc

            # finalproc

            # enum

            # common

            # calls

            # if not isinstance(entity, _can_have_contains):
            #     return

            # if not (contains := self.contains_query.maybe_first(cursor)):
            #     return

            if not cursor.goto_next_sibling():
                break

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
        ancestor_module = submodule.node.child_by_field_name("ancestor")
        parent_submod = submodule.node.child_by_field_name("parent")

        return FortranSubmodule(
            self,
            submodule,
            parent,
            name=self._get_name(submodule),
            ancestor_module=maybe_decode(ancestor_module),
            parent_submod=maybe_decode(parent_submod),
        )

    def parse_attributes(
        self, parent: FortranCodeUnit | FortranBlockData, cursor: TreeCursor
    ):
        attribute = decode(cursor.node.child(0)).lower()

        names = []
        for node in traverse_children(cursor):
            if node.type == "identifier":
                names.append(decode(node).lower())
            elif node.type == "sized_declarator":
                names.append(decode(node.child(0)).lower())
                attribute += decode(node.child(1)).lower()

        for name in names:
            parent.attr_dict[name].append(attribute)

    def parse_block_data(self, parent, node):
        pass

    def parse_associate(self, parent, node):
        pass

    def parse_subroutine(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> FortranSubroutine:
        attributes = []
        arguments = []
        bindC = None

        for node in traverse_children(cursor):
            if node.type == "procedure_qualifier":
                attributes.append(decode(node).lower())
            elif node.type == "parameters":
                arguments = [decode(arg).lower() for arg in node.named_children]
            elif node.type == "language_binding":
                bindC = decode(node)

        return FortranSubroutine(
            self,
            cursor,
            parent=parent,
            inherited_permission=parent.permission,
            name=self._get_name(cursor),
            attributes=",".join(attributes),
            arguments=arguments,
            bindC=bindC,
        )

    def parse_function(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> FortranFunction:
        attributes = []
        result_name = None
        result_type = None
        arguments = []
        bindC = None

        for node in traverse_children(cursor):
            if node.type == "procedure_qualifier":
                attributes.append(decode(node).lower())
            elif node.type in ("intrinsic_type", "derived_type"):
                result_type = decode(node).lower()
            elif node.type == "parameters":
                arguments = [decode(arg).lower() for arg in node.named_children]
            elif node.type == "function_result":
                result_name = decode(node.named_children[0]).lower()
            elif node.type == "language_binding":
                bindC = decode(node)

        return FortranFunction(
            self,
            cursor,
            parent=parent,
            inherited_permission=parent.permission,
            name=self._get_name(cursor),
            attributes=",".join(attributes),
            result_name=result_name,
            result_type=result_type,
            arguments=arguments,
            bindC=bindC,
        )

    def parse_module_procedure(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> FortranModuleProcedureImplementation:
        attributes = []

        for node in traverse_children(cursor):
            if node.type == "procedure_qualifier":
                attributes.append(decode(node))

        return FortranModuleProcedureImplementation(
            self,
            cursor,
            parent=parent,
            names=self._get_name(cursor),
        )

    def parse_variable(
        self, parent: FortranContainer, cursor: TreeCursor, inherit_permission: str
    ) -> List[FortranVariable]:
        attributes = []
        permission = inherit_permission
        intent = ""
        optional = False
        permission = inherit_permission
        parameter = False

        vartype = maybe_decode(cursor.node.child_by_field_name("type"))

        variables = []

        for node in traverse_children(cursor):
            if node.type == "type_qualifier":
                # Lowercase and remove whitespace so checking intent is cleaner
                tmp_attrib_lower = decode(node).lower().replace(" ", "")
                if tmp_attrib_lower in ["public", "private", "protected"]:
                    permission = tmp_attrib_lower
                elif tmp_attrib_lower == "optional":
                    optional = True
                elif tmp_attrib_lower == "parameter":
                    parameter = True
                elif tmp_attrib_lower == "intent(in)":
                    intent = "in"
                elif tmp_attrib_lower == "intent(out)":
                    intent = "out"
                elif tmp_attrib_lower == "intent(inout)":
                    intent = "inout"
                else:
                    attributes.append(decode(node))

            if node.type == "method_name":
                variables.append(
                    FortranVariable(
                        decode(node),
                        vartype="procedure",
                        parent=parent,
                        attribs=attributes,
                    )
                )

        for declarator in cursor.node.children_by_field_name("declarator"):
            initial = None
            points = False
            if declarator.type == "identifier":
                name = decode(declarator)
            elif declarator.type == "sized_declarator":
                name = decode(declarator.child(0))
            elif declarator.type == "init_declarator":
                name = decode(declarator.child_by_field_name("left"))
                initial = decode(declarator.child_by_field_name("right"))
            elif declarator.type == "pointer_init_declarator":
                name = decode(declarator.child_by_field_name("left"))
                initial = decode(declarator.child_by_field_name("right"))
                points = True
            variables.append(
                FortranVariable(
                    name=name,
                    parent=parent,
                    vartype=vartype,
                    attribs=attributes,
                    intent=intent,
                    optional=optional,
                    permission=permission,
                    parameter=parameter,
                    initial=initial,
                    points=points,
                )
            )

        return variables

    def parse_namelist(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> List[FortranNamelist]:
        namelists = []

        # We need a cursor on the `namelist` node itself in order to get the
        # docstring correctly
        parent_cursor = cursor.node.parent.walk()

        while cursor.goto_next_sibling():
            if cursor.node.type != "variable_group":
                continue
            name = None
            variables = []
            for node in traverse_children(cursor):
                if node.type == "name":
                    name = decode(node)
                elif node.type == "identifier":
                    variables.append(decode(node))

            namelists.append(
                FortranNamelist(
                    parent_cursor,
                    self,
                    parent=parent,
                    name=name,
                    vars=variables,
                )
            )

        return namelists

    def parse_derived_type(self, parent: FortranContainer, cursor: TreeCursor):
        type_attributes = []
        type_extends = None
        type_permission = parent.permission
        type_parameters = []
        name = None

        for node in traverse_children(cursor):
            if node.type == "access_specifier":
                type_permission = decode(node)
            elif node.type == "base_type_specifier":
                for base in traverse_children(cursor):
                    if base.type == "identifier":
                        type_extends = decode(base)
            elif node.type == "type_name":
                name = decode(node)
            elif node.type == "derived_type_parameter_list":
                type_parameters = SPLIT_RE.split(decode(node).strip())
            elif node.type in ("abstract_specifier", "language_binding"):
                type_attributes.append(decode(node))

        return FortranType(
            self,
            cursor,
            parent,
            inherited_permission=type_permission,
            name=name,
            attributes=type_attributes,
            parameters=type_parameters,
            extends=type_extends,
        )

    def parse_interface(self, parent: FortranCodeUnit, cursor: TreeCursor):
        abstract = has_named_child(cursor, "abstract_specifier")
        name = ""
        for child in cursor.node.named_children:
            if child.type in ("name", "assignment", "operator", "defined_io_procedure"):
                name = decode(child)

        interface = FortranInterface(
            self,
            cursor,
            parent,
            inherited_permission=parent.permission,
            name=name,
            abstract=abstract,
        )

        if abstract:
            parent.absinterfaces.extend(interface.contents)
        elif name:
            parent.interfaces.append(interface)
        else:
            parent.interfaces.extend(interface.contents)

    def parse_bound_procedure(self, parent, node):
        pass

    def parse_final_procedure(self, parent, node):
        pass

    def parse_enum(self, parent: FortranContainer, cursor: TreeCursor):
        return FortranEnum(self, cursor, parent, parent.permission)

    def parse_use_statement(
        self, parent: FortranContainer, cursor: TreeCursor
    ) -> ModuleUses:
        name = ""
        items = []
        only = False
        for node in traverse_children(cursor):
            if node.type == "module_name":
                name = decode(node)
            elif node.type == "use_alias":
                items.append(_from_use_alias(node))
            elif node.type == "included_items":
                only = True
                for item in node.named_children:
                    if item.type == "use_alias":
                        items.append(_from_use_alias(item))
                    else:
                        items.append(ModuleUsesItem(decode(item)))

        return ModuleUses(name, only, items)


def _from_use_alias(use_alias: Node) -> ModuleUsesItem:
    return ModuleUsesItem(decode(use_alias.child(2)), decode(use_alias.child(0)))
