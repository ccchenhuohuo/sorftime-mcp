from dataclasses import dataclass


@dataclass(frozen=True)
class DomainOption:
    id: int
    code: str
    name: str
    supports_historical_backfill: bool = True


DOMAIN_OPTIONS: tuple[DomainOption, ...] = (
    DomainOption(1, "US", "美国"),
    DomainOption(2, "GB", "英国"),
    DomainOption(3, "DE", "德国"),
    DomainOption(4, "FR", "法国"),
    DomainOption(5, "IN", "印度", False),
    DomainOption(6, "CA", "加拿大"),
    DomainOption(7, "JP", "日本"),
    DomainOption(8, "ES", "西班牙"),
    DomainOption(9, "IT", "意大利"),
    DomainOption(10, "MX", "墨西哥"),
    DomainOption(11, "AE", "阿联酋", False),
    DomainOption(12, "AU", "澳大利亚", False),
    DomainOption(13, "BR", "巴西", False),
    DomainOption(14, "SA", "沙特阿拉伯", False),
)

DOMAIN_ID_DESCRIPTION = (
    "Amazon marketplace domain id. Mapping: "
    + ", ".join(f"{option.id}={option.code}({option.name})" for option in DOMAIN_OPTIONS)
    + ". Historical backfill is not supported for IN, AE, AU, BR, or SA."
)


def domains_payload() -> list[dict[str, object]]:
    return [
        {
            "id": option.id,
            "code": option.code,
            "name": option.name,
            "supportsHistoricalBackfill": option.supports_historical_backfill,
        }
        for option in DOMAIN_OPTIONS
    ]

