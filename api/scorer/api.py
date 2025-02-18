"""
The scorer API module
"""
from typing import List, Optional

from ceramic_cache.api import router as ceramic_cache_router
from django_ratelimit.exceptions import Ratelimited
from ninja import NinjaAPI
from ninja.openapi.schema import OpenAPISchema
from ninja.operation import Operation
from ninja.types import DictStrAny
from registry.api.v1 import analytics_router, feature_flag_router
from registry.api.v1 import router as registry_router_v1
from registry.api.v2 import router as registry_router_v2


###############################################################################
# The following constructs will override the default OpenAPI schema generation
# The purpose if to enable adding a custom name to the security schema defined
# by an async function used in an async api.
# The default NinjaAPI implementation will use the name of the class or
# entity (which in case of a function is `function`), hence creating confusion
# (duplicate securitySchema Types) in the generated OpenAPI live docs.
# Our implementation will use the attribute `openapi_security_schema_name` of
# the auth object if it exists (this is our customisation), otherwise it will use
#  the class name (which is what NinjaAPI does right now).
###############################################################################
class ScorerOpenAPISchema(OpenAPISchema):
    def operation_security(self, operation: Operation) -> Optional[List[DictStrAny]]:
        if not operation.auth_callbacks:
            return None
        result = []
        for auth in operation.auth_callbacks:
            if hasattr(auth, "openapi_security_schema"):
                scopes: List[DictStrAny] = []  # TODO: scopes
                name = (
                    auth.openapi_security_schema_name
                    if hasattr(auth, "openapi_security_schema_name")
                    else auth.__class__.__name__
                )
                result.append({name: scopes})  # TODO: check if unique
                self.securitySchemes[name] = auth.openapi_security_schema  # type: ignore
        return result


def scorer_get_schema(api: "NinjaAPI", path_prefix: str = "") -> ScorerOpenAPISchema:
    openapi = ScorerOpenAPISchema(api, path_prefix)
    return openapi


class ScorerApi(NinjaAPI):
    def get_openapi_schema(self, path_prefix: Optional[str] = None) -> OpenAPISchema:
        if path_prefix is None:
            path_prefix = self.root_path
        return scorer_get_schema(api=self, path_prefix=path_prefix)


###############################################################################
# End of customisinz securitySchema for OpenAPI
###############################################################################


registry_api_v1 = ScorerApi(
    urls_namespace="registry", title="Scorer API", version="1.0.0"
)
registry_api_v2 = NinjaAPI(
    urls_namespace="registry_v2", title="Scorer API", version="2.0.0"
)


@registry_api_v1.exception_handler(Ratelimited)
def service_unavailable(request, _):
    return registry_api_v1.create_response(
        request,
        {"detail": "You have been rate limited!"},
        status=429,
    )


registry_api_v1.add_router(
    "/registry/", registry_router_v1, tags=["Score your passport"]
)

feature_flag_api = NinjaAPI(urls_namespace="feature")
feature_flag_api.add_router("", feature_flag_router)

registry_api_v2.add_router("", registry_router_v2, tags=["Score your passport"])

ceramic_cache_api = NinjaAPI(urls_namespace="ceramic-cache", docs_url=None)
ceramic_cache_api.add_router("", ceramic_cache_router)

analytics_api = NinjaAPI(urls_namespace="analytics", title="Data Analytics API")
analytics_api.add_router("", analytics_router)
