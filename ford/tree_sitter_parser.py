from ford.sourceform import (
    FortranBase,
    FortranContainer,
    FortranModule,
    FortranFunction,
    remove_prefixes,
    _can_have_contains,
)
from typing import List

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


class Query:
    def __init__(self, language: Language, query: str):
        self.query = language.query(query)

    def __call__(self, node: Node) -> List[Node]:
        return [capture for capture, _ in self.query.captures(node)]

    def first(self, node: Node):
        return self(node) or None


class TreeSitterParser:
    def __init__(self, free_form: bool = True, encoding: str = "utf-8"):
        self.encoding = encoding

        self.language = FREE_FORM_LANGUAGE if free_form else FIXED_FORM_LANGUAGE
        self.parser = FREE_FORM_PARSER if free_form else FIXED_FORM_PARSER

        self.program_query = self.language.query("(program) @program.def")
        self.module_query = self.language.query("(module) @module.def")
        self.module_name_query = self.language.query("(module_statement (name) @name)")

        self.contains_query = self.language.query("(internal_procedures) @contains")

        self.function_query = self.language.query("(function) @function.def")
        self.function_result_query = self.language.query(
            "(function_result (identifier) @function.result)"
        )
        self.function_parameters_query = self.language.query(
            "(function_statement parameters: (parameters) @function.arg)"
        )
        self.function_attributes_query = self.language.query(
            "(function_statement (procedure_qualifier) @function.attrs)"
        )
        self.function_binding_query = self.language.query(
            "(language_binding) @function.bind"
        )

        self.name_query = self.language.query("(name) @name")

    def _get_name(self, node):
        name_capture, _ = self.name_query.captures(node)[0]
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
            for module, _ in self.module_query.captures(source):
                entity.modules.append(
                    FortranModule(
                        self,
                        module,
                        parent=entity,
                        name=self._get_name(module),
                    )
                )

        if not isinstance(entity, _can_have_contains):
            return

        if not (contains := self.contains_query.captures(source)):
            return

        contains = contains[0][0]

        if hasattr(entity, "functions"):
            for function, _ in self.function_query.captures(contains):
                entity.functions.append(self.parse_function(entity, function))

    def parse_function(self, parent: FortranContainer, function: Node):
        attributes = [
            attr[0].text.decode()
            for attr in self.function_attributes_query.captures(function)
        ]
        name = self._get_name(function)
        arguments = self.function_parameters_query.captures(function)[0][
            0
        ].text.decode()

        if result_capture := self.function_result_query.captures(function):
            result = result_capture[0][0].text.decode()
        else:
            result = None

        if binding := self.function_binding_query.captures(function):
            bind = binding[0][0].text.decode()
        else:
            bind = None

        return FortranFunction(
            self,
            function,
            parent=parent,
            name=name,
            attributes="\n".join(attributes),
            result=result,
            arguments=arguments,
            bindC=bind,
        )
