from flask import Flask, render_template, request
import re

app = Flask(__name__)

# -----------------------------------
# KEYWORDS
# -----------------------------------

KEYWORDS = {
    "int", "float", "double", "char", "void",
    "if", "else", "for", "while", "return",
    "break", "continue", "switch", "case",
    "default", "do", "long", "short",
    "unsigned", "signed", "const"
}


# -----------------------------------
# ANALYZE SOURCE CODE
# -----------------------------------

def analyze_code(source_code):

    symbols = []
    errors = []

    # Scope stack
    scopes = [{}]
    scope_names = ["Global"]

    current_scope = 0
    address = 1000

    # Variable declaration pattern
    declaration_pattern = re.compile(
        r'\b(int|float|double|char)\s+'
        r'([a-zA-Z_][a-zA-Z0-9_]*)'
    )

    # Identifier pattern
    identifier_pattern = re.compile(
        r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
    )

    lines = source_code.splitlines()

    # -----------------------------------
    # PROCESS EACH LINE
    # -----------------------------------

    for line_number, original_line in enumerate(lines, start=1):

        # Remove comments
        line = re.sub(r'//.*', '', original_line)

        # -----------------------------------
        # SCOPE MANAGEMENT
        # -----------------------------------

        for character in line:

            if character == '{':

                current_scope += 1

                scopes.append({})

                scope_names.append(
                    f"Scope{current_scope}"
                )

            elif character == '}':

                if current_scope > 0:

                    scopes.pop()
                    scope_names.pop()

                    current_scope -= 1

        current_scope_name = scope_names[current_scope]

        # -----------------------------------
        # IDENTIFY DECLARATIONS
        # -----------------------------------

        declarations = declaration_pattern.findall(line)

        declared_names = set()

        for data_type, name in declarations:

            declared_names.add(name)

            # Check redeclaration
            if name in scopes[current_scope]:

                errors.append({
                    "line": line_number,
                    "message":
                    f"Redeclaration of '{name}' "
                    f"in {current_scope_name}"
                })

            else:

                symbol = {
                    "name": name,
                    "type": data_type,
                    "scope": current_scope_name,
                    "line": line_number,
                    "address": address
                }

                scopes[current_scope][name] = symbol

                symbols.append(symbol)

                address += 4

        # -----------------------------------
        # IDENTIFIER USAGE
        # -----------------------------------

        identifiers = identifier_pattern.findall(line)

        for identifier in identifiers:

            # Ignore keywords
            if identifier in KEYWORDS:
                continue

            # Ignore identifiers that were declared
            if identifier in declared_names:
                continue

            # Ignore function names
            if re.search(
                r'\b' + re.escape(identifier) + r'\s*\(',
                line
            ):
                continue

            # Search current scope and outer scopes
            found = False

            for scope_index in range(
                current_scope,
                -1,
                -1
            ):

                if identifier in scopes[scope_index]:

                    found = True
                    break

            # Undeclared identifier
            if not found:

                errors.append({
                    "line": line_number,
                    "message":
                    f"Undeclared identifier "
                    f"'{identifier}'"
                })

    return symbols, errors


# -----------------------------------
# HOME PAGE
# -----------------------------------

@app.route("/", methods=["GET", "POST"])
def index():

    code = ""

    symbols = []
    errors = []

    analyzed = False

    # -----------------------------------
    # WHEN ANALYZE BUTTON IS CLICKED
    # -----------------------------------

    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        )

        symbols, errors = analyze_code(
            code
        )

        analyzed = True

    return render_template(
        "index.html",
        code=code,
        symbols=symbols,
        errors=errors,
        analyzed=analyzed
    )


# -----------------------------------
# START FLASK SERVER
# -----------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )