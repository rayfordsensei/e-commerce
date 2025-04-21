from spectree import SecurityScheme, SecuritySchemeData, SpecTree
from spectree.models import SecureType

scheme_data = SecuritySchemeData.parse_obj({  # pyright:ignore[reportDeprecated]
    "type": SecureType.HTTP.value,
    "scheme": "bearer",
    "bearerFormat": "JWT",
})

api = SpecTree(
    "falcon-asgi",
    title="E-Commerce API",
    version="1.0.0",
    path="apidoc",  # -> /apidoc/swagger, /apidoc/redoc, /apidoc/scalar
    security_schemes=[
        SecurityScheme(
            name="bearerAuth",
            data=scheme_data,
        )
    ],
    mode="strict",
)
