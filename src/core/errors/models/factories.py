from __future__ import annotations

from src.core.errors.codes.common_error_codes import CommonErrorCodes
from src.core.errors.codes.external_error_codes import ExternalErrorCodes
from src.core.errors.models.iflow_error import IFlowError


def auth_error(
    code: str = "INVALID_CREDENTIALS",
    message: str = "Not authenticated.",
) -> IFlowError:
    return IFlowError(code=code, message=message, category="auth", status=401)


def permission_error(
    code: str = CommonErrorCodes.FORBIDDEN,
    message: str = "You do not have permission to perform this action.",
) -> IFlowError:
    return IFlowError(
        code=code, message=message, category="permission", status=403
    )


def not_found_error(
    code: str = CommonErrorCodes.RESOURCE_NOT_FOUND,
    message: str = "The requested resource was not found.",
) -> IFlowError:
    return IFlowError(
        code=code, message=message, category="not_found", status=404
    )


def validation_error(
    code: str = CommonErrorCodes.VALIDATION_ERROR,
    message: str = "The request contains invalid data.",
) -> IFlowError:
    return IFlowError(
        code=code, message=message, category="validation", status=422
    )


def business_error(
    code: str = CommonErrorCodes.BUSINESS_RULE_VIOLATION,
    message: str = "A business rule was violated.",
    status: int = 409,
) -> IFlowError:
    return IFlowError(
        code=code, message=message, category="business", status=status
    )


def external_error(
    code: str = ExternalErrorCodes.EXTERNAL_SERVICE_ERROR,
    message: str = "An external service failed.",
) -> IFlowError:
    return IFlowError(
        code=code, message=message, category="external", status=502
    )


def infrastructure_error(
    code: str = CommonErrorCodes.INFRASTRUCTURE_ERROR,
    message: str = "An infrastructure error occurred.",
) -> IFlowError:
    return IFlowError(
        code=code, message=message, category="infrastructure", status=503
    )
