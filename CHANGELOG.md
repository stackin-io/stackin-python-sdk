# Changelog — invoice (SDK)

## Não lançado

### Alterado (breaking)
- SDK virou um client HTTP fino do `invoice-api` — não fala mais direto com SEFAZ/ADN. Todo o protocolo (NFe/nfse, XSD, assinatura) migrou pra lá.
- `Invoice.issue()` agora recebe poucos campos de negócio (`client_name`, `tax_id`, `description`, `amount`, `address`) em vez de um documento técnico completo (`NFeDoc`/`DPS`).
- `Address` (pydantic) substitui os parâmetros soltos `state`/`municipality_code` — `address.state` alimenta NF-e, `address.city_code` alimenta NFS-e; todo o resto é opcional.
- Todos os nomes de campo em inglês (`client_name`, `tax_id`, `reason`...).

### Removido
- `nfe`/`nfse` (clients SOAP/REST completos), `schemas/nfse_servico.py`, `nfse_valores.py`, `nfse_pessoa.py`, `nfe_pessoa.py` (schemas 100% fiéis ao XSD) — todos moveram pra `invoice-api/app/providers/`.
- Dependência de certificado/`Config` do lado do cliente.

### Adicionado
- `InvalidDocumentError` → depois removido de novo junto com a validação de schema (não se aplica mais, sem documento técnico no SDK).
- `ConnectionFailedError` tratado corretamente mesmo quando a API responde corpo não-JSON no erro (antes explodia com `JSONDecodeError` cru).
