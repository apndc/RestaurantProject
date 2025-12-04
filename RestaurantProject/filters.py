# Formatting Filters
def register_filters(app):
    @app.template_filter('phone_format')
    def format_phone(digits: str) -> str:
        d = "".join(ch for ch in digits if ch.isdigit())
        return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"

    @app.template_filter('name_format')
    def format_name(name: str) -> str:
        return name.capitalize()
    
    # Dollar Filter for Formatting
    @app.template_filter('dollars')
    def dollars(value):
        return f"${value:,.2f}"
    
    @app.template_filter('name_title')
    def format_name(name: str) -> str:
        return name.upper()