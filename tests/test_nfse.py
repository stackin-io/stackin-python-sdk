"""NFS-e DPS fields: the body issue() and validate() send and the shapes refused."""

import json
import unittest
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import patch

from pydantic import ValidationError

from stackin import (
    Address,
    Company,
    DocumentType,
    FiscalReference,
    Invoice,
    Items,
    NbsSuggestions,
)
from stackin.br import (
    ApproximateTaxes,
    Construction,
    DeductionDocument,
    DeductionSupplier,
    Deductions,
    Event,
    FederalTaxes,
    ForeignTrade,
    IbsCbs,
    IbsCbsGovernment,
    IbsCbsRecipient,
    IssDetails,
    IssSuspension,
    MunicipalNfse,
    NfseDetails,
    NfseIntermediary,
    NfseProvider,
    OtherDfe,
    PersonAddress,
    PisCofins,
    Product,
    RealEstate,
    RealEstateLease,
    RealEstateUnit,
    References,
    ServiceAddress,
    Substitution,
)
from tests.test_reference import FakeResponse

KEY = "351234" + "ABCDEFGH123456" + "0" * 30
NFE_KEY = "3" * 44
BASE = "https://sdk.test/api/v1"


def service(**fields):
    line: dict[str, Any] = {
        "description": "Consultoria",
        "unit_price": Decimal("100.00"),
        "service_code": "1.07",
    }
    line.update(fields)
    return Product(**line)


class IssueCase(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def body(self, method="issue", **fields):
        call: dict[str, Any] = {
            "document_type": DocumentType.NFSE,
            "client_name": "Tomador",
            "tax_id": "11222333000181",
            "items": [service()],
        }
        call.update(fields)
        answer = {"valid": True} if method == "validate" else {}
        with patch.object(self.client, "_request", return_value=answer) as sent:
            getattr(self.client, method)(**call)
        return sent.call_args.kwargs["json"]


class TestBody(IssueCase):
    def test_unset_fields_are_not_in_the_body(self):
        body = self.body()

        for key in (
            "nfse",
            "recipient_municipal_registration",
            "foreign_id_missing_reason",
        ):
            self.assertNotIn(key, body)
        line = body["items"][0]
        for key in ("nbs", "municipal_service_code", "internal_code"):
            self.assertNotIn(key, line)
        self.assertNotIn("conditional_discount", line)

    def test_an_empty_nfse_is_not_sent(self):
        self.assertNotIn("nfse", self.body(nfse=NfseDetails()))

    def test_line_fields_go_out_by_their_api_names(self):
        line = self.body(
            items=[
                service(
                    nbs="1.1502.10.00",
                    municipal_service_code="001",
                    internal_code="SRV01",
                    conditional_discount=Decimal("5.5"),
                )
            ]
        )["items"][0]

        self.assertEqual(line["nbs"], "1.1502.10.00")
        self.assertEqual(line["municipal_service_code"], "001")
        self.assertEqual(line["internal_code"], "SRV01")
        self.assertEqual(line["conditional_discount"], "5.5")

    def test_recipient_fields_go_out(self):
        body = self.body(
            recipient_municipal_registration="12345",
            foreign_id_missing_reason=2,
        )

        self.assertEqual(body["recipient_municipal_registration"], "12345")
        self.assertEqual(body["foreign_id_missing_reason"], 2)

    def test_the_address_carries_complement_and_the_foreign_fields(self):
        address = Address(
            state="EX",
            country_iso2="US",
            postal_code="10001",
            province="NY",
            complement="Suite 4",
            street="5th Avenue",
            number="1",
            neighborhood="Midtown",
            city="New York",
        )
        body = self.body(
            tax_id=None,
            foreign_id_missing_reason=1,
            recipient_address=address,
        )

        sent = body["recipient_address"]
        self.assertEqual(sent["country_iso2"], "US")
        self.assertEqual(sent["postal_code"], "10001")
        self.assertEqual(sent["province"], "NY")
        self.assertEqual(sent["complement"], "Suite 4")
        self.assertNotIn("tax_id", body)

    def test_a_retained_nfse_to_a_recipient_abroad_needs_no_cep(self):
        address = Address(
            state="EX",
            country_iso2="PT",
            postal_code="1000",
            province="Lisboa",
            street="Rua",
            number="1",
            neighborhood="Centro",
            city="Lisboa",
        )

        body = self.body(
            tax_id=None,
            foreign_id="PT12345678",
            recipient_address=address,
            items=[service(tax_retained=True)],
        )

        self.assertTrue(body["items"][0]["tax_retained"])

    def test_validate_takes_the_same_fields(self):
        body = self.body(
            method="validate",
            nfse=NfseDetails(competence_date=date(2026, 11, 1)),
            recipient_municipal_registration="9",
        )

        self.assertEqual(body["nfse"], {"competence_date": "2026-11-01"})
        self.assertEqual(body["recipient_municipal_registration"], "9")


class TestNfseObject(IssueCase):
    def test_every_group_goes_out_as_json(self):
        details = NfseDetails(
            approximate_taxes=ApproximateTaxes(
                federal_percent=Decimal("4.5"), state_percent=0
            ),
            competence_date=date(2026, 11, 1),
            service_city_code="3550308",
            iss=IssDetails(
                taxation="taxable",
                rate=Decimal("2.5"),
                retention="none",
                suspension=IssSuspension(type="judicial", process_number="1" * 30),
            ),
            federal=FederalTaxes(
                pis_cofins=PisCofins(
                    cst="01", base=Decimal("100"), pis_rate=Decimal("0.65")
                ),
                irrf_withheld=Decimal("1.50"),
            ),
            deductions=Deductions(
                documents=[
                    DeductionDocument(
                        type=2,
                        nfse_key=KEY,
                        issue_date=date(2026, 10, 1),
                        total_amount=Decimal("50"),
                        deducted_amount=Decimal("40"),
                    ),
                    DeductionDocument(
                        type=7,
                        municipal_nfse=MunicipalNfse(
                            city_code="3550308", number="12", verification_code="AB1"
                        ),
                        issue_date=date(2026, 10, 2),
                        total_amount=Decimal("10"),
                        deducted_amount=Decimal("5"),
                        supplier=DeductionSupplier(
                            tax_id="11222333000181",
                            name="Fornecedor",
                            address=PersonAddress(
                                street="Rua",
                                number="1",
                                neighborhood="Centro",
                                city_code="3550308",
                                zip_code="01001000",
                            ),
                        ),
                    ),
                ]
            ),
            substitution=Substitution(
                access_key=KEY, reason_code="99", reason="Correcao do valor do servico"
            ),
            construction=Construction(work_id_type="cno", work_id="123"),
            event=Event(
                name="Festival",
                start_date=date(2026, 11, 1),
                end_date=date(2026, 11, 2),
                address=ServiceAddress(
                    zip_code="01001000",
                    street="Rua",
                    number="1",
                    neighborhood="Centro",
                ),
            ),
            references=References(order_number="PO-1", order_items=["a", "b"]),
            intermediary=NfseIntermediary(
                foreign_id="NIF123",
                name="Agent Ltd",
                address=PersonAddress(
                    street="Road",
                    number="2",
                    neighborhood="Soho",
                    country_code="GB",
                    postal_code="W1",
                    city="London",
                    state="England",
                ),
            ),
            foreign_trade=ForeignTrade(
                service_mode=1,
                relationship=0,
                currency_code="220",
                foreign_amount=Decimal("20.00"),
                provider_support=1,
                recipient_support=1,
                temporary_goods=1,
                share_with_mdic=False,
            ),
        )

        sent = self.body(nfse=details)["nfse"]

        self.assertEqual(json.loads(json.dumps(sent)), sent)
        self.assertEqual(sent["approximate_taxes"]["federal_percent"], "4.5")
        self.assertEqual(sent["competence_date"], "2026-11-01")
        self.assertEqual(sent["service_city_code"], "3550308")
        self.assertEqual(sent["iss"]["rate"], "2.5")
        self.assertEqual(sent["iss"]["suspension"]["type"], "judicial")
        self.assertEqual(sent["federal"]["pis_cofins"]["pis_rate"], "0.65")
        self.assertEqual(sent["federal"]["irrf_withheld"], "1.50")
        documents = sent["deductions"]["documents"]
        self.assertEqual(documents[0]["issue_date"], "2026-10-01")
        self.assertEqual(documents[0]["total_amount"], "50")
        self.assertEqual(documents[1]["municipal_nfse"]["number"], "12")
        self.assertEqual(documents[1]["supplier"]["address"]["city_code"], "3550308")
        self.assertEqual(sent["substitution"]["reason_code"], "99")
        self.assertEqual(
            sent["construction"], {"work_id_type": "cno", "work_id": "123"}
        )
        self.assertEqual(sent["event"]["start_date"], "2026-11-01")
        self.assertEqual(sent["references"]["order_items"], ["a", "b"])
        self.assertEqual(sent["intermediary"]["address"]["country_code"], "GB")
        self.assertEqual(sent["foreign_trade"]["foreign_amount"], "20.00")
        self.assertIs(sent["foreign_trade"]["share_with_mdic"], False)
        self.assertNotIn("service_country_code", sent)

    def test_provider_recipient_caepf_and_other_dfe_go_out(self):
        sent = self.body(
            nfse=NfseDetails(
                provider=NfseProvider(
                    caepf="12345678901234",
                    phone="+55 11 99999-0000",
                    email="a@b.com",
                ),
                recipient_caepf="43210987654321",
                deductions=Deductions(
                    documents=[
                        DeductionDocument(
                            type=99,
                            description="Other",
                            other_dfe=OtherDfe(key="K" * 50, description="Receipt"),
                            issue_date=date(2026, 10, 1),
                            total_amount=Decimal("50"),
                            deducted_amount=Decimal("40"),
                        )
                    ]
                ),
            )
        )["nfse"]

        self.assertEqual(
            sent["provider"],
            {
                "caepf": "12345678901234",
                "phone": "+55 11 99999-0000",
                "email": "a@b.com",
            },
        )
        self.assertEqual(sent["recipient_caepf"], "43210987654321")
        self.assertEqual(
            sent["deductions"]["documents"][0]["other_dfe"],
            {"key": "K" * 50, "description": "Receipt"},
        )

    def test_unset_fields_are_left_out_of_each_group(self):
        sent = self.body(nfse=NfseDetails(iss=IssDetails(rate=Decimal("2"))))["nfse"]

        self.assertEqual(sent, {"iss": {"rate": "2"}})


class TestRefusedShapes(unittest.TestCase):
    def refused(self, build):
        with self.assertRaises(ValidationError):
            build()

    def test_unknown_fields_are_refused(self):
        self.refused(lambda: NfseDetails(**{"unknown": 1}))
        self.refused(lambda: IssDetails(**{"rate": 1, "other": 2}))

    def test_code_sets(self):
        self.refused(lambda: IssDetails(taxation="free"))
        self.refused(lambda: IssDetails(retention="both"))
        self.refused(lambda: IssDetails(immunity_type=6))
        self.refused(lambda: PisCofins(cst="10"))
        self.refused(lambda: Substitution(access_key=KEY, reason_code="06"))
        self.refused(lambda: NfseIntermediary(name="x", foreign_id_missing_reason=0))
        self.refused(lambda: IbsCbsGovernment(operation_type="6"))

    def test_patterns_and_lengths(self):
        self.refused(lambda: NfseDetails(service_city_code="123"))
        self.refused(lambda: NfseDetails(service_country_code="br"))
        self.refused(lambda: IssSuspension(type="judicial", process_number="1"))
        self.refused(lambda: Substitution(access_key="1", reason_code="01"))
        self.refused(
            lambda: Substitution(access_key=KEY, reason_code="99", reason="short")
        )
        self.refused(lambda: References(order_items=[]))
        self.refused(lambda: References(order_number=""))
        self.refused(
            lambda: ServiceAddress(
                zip_code="1", street="a", number="1", neighborhood="b"
            )
        )

    def test_caepf_and_other_dfe_shapes(self):
        self.refused(lambda: NfseProvider(caepf="123"))
        self.refused(lambda: NfseProvider(unknown="x"))
        self.refused(lambda: NfseDetails(recipient_caepf="1234567890123a"))
        self.refused(lambda: OtherDfe(key="", description="x"))
        self.refused(lambda: OtherDfe(key="K" * 51, description="x"))
        self.refused(lambda: OtherDfe(key="k", description=""))
        self.refused(lambda: OtherDfe(key="k", description="d" * 256))
        NfseProvider()

    def test_numeric_limits(self):
        self.refused(lambda: ApproximateTaxes(simples_percent=Decimal("100")))
        self.refused(lambda: ApproximateTaxes(federal_percent=Decimal("1.234")))
        self.refused(lambda: ApproximateTaxes(federal_amount=-1))
        self.refused(lambda: IssDetails(rate=Decimal("5.01")))
        self.refused(lambda: IssDetails(rate=0))
        self.refused(lambda: FederalTaxes(irrf_withheld=0))

    def test_foreign_trade_codes(self):
        base: dict[str, Any] = {
            "service_mode": 1,
            "relationship": 0,
            "currency_code": "220",
            "foreign_amount": Decimal("1"),
            "provider_support": 1,
            "recipient_support": 1,
            "temporary_goods": 1,
        }
        ForeignTrade(**base)
        for field, value in (
            ("service_mode", 0),
            ("relationship", 7),
            ("provider_support", 9),
            ("recipient_support", 27),
            ("temporary_goods", 4),
            ("currency_code", "US"),
        ):
            with self.subTest(field=field):
                self.refused(lambda: ForeignTrade(**{**base, field: value}))

    def test_deduction_document_types(self):
        common = {
            "issue_date": date(2026, 1, 1),
            "total_amount": Decimal("1"),
            "deducted_amount": Decimal("1"),
        }
        DeductionDocument(type=105, nfe_key=NFE_KEY, **common)
        self.refused(lambda: DeductionDocument(type=10, nfe_key=NFE_KEY, **common))
        self.refused(lambda: DeductionDocument(type=1, nfe_key="1", **common))

    def test_the_cross_field_rules_are_the_apis(self):
        NfseDetails(service_city_code="3550308", service_country_code="US")
        ApproximateTaxes(simples_percent=Decimal("1"), federal_percent=Decimal("1"))
        Deductions(percent=Decimal("1"), amount=Decimal("1"))
        Construction()
        Event(name="x", start_date=date(2026, 1, 1), end_date=date(2026, 1, 2))
        NfseIntermediary(name="x")


class TestIbsCbs(IssueCase):
    def test_the_nfse_extras_go_out_under_br(self):
        ibs = IbsCbs(
            cst="000",
            classification="000001",
            operation_indicator="100301",
            personal_use=True,
            government=IbsCbsGovernment(operation_type="1", entity_type="4"),
            referenced_nfse=[KEY],
            recipient=IbsCbsRecipient(
                tax_id="11222333000181", name="Destino", email="a@b.co"
            ),
            real_estate=RealEstate(
                lease=RealEstateLease(
                    co_ownership_percent=100,
                    total_amount=1000,
                    original_due_date=date(2026, 12, 5),
                ),
                units=[RealEstateUnit(cib="1234567A")],
            ),
            regular_taxation={"cst": "000", "classification": "000001"},
            deferral={"state_percent": 1, "city_percent": 2, "cbs_percent": 3},
            presumed_credit="01",
        )

        sent = self.body(items=[service(nbs="115021000", ibs_cbs=ibs)])["items"][0][
            "product"
        ]["br"]["ibs_cbs"]

        self.assertEqual(json.loads(json.dumps(sent)), sent)
        self.assertEqual(sent["cst"], "000")
        self.assertIs(sent["personal_use"], True)
        self.assertEqual(
            sent["government"], {"operation_type": "1", "entity_type": "4"}
        )
        self.assertEqual(sent["referenced_nfse"], [KEY])
        self.assertEqual(sent["recipient"]["tax_id"], "11222333000181")
        self.assertEqual(
            sent["real_estate"]["lease"]["original_due_date"], "2026-12-05"
        )
        self.assertEqual(sent["real_estate"]["units"], [{"cib": "1234567A"}])
        self.assertEqual(sent["regular_taxation"]["classification"], "000001")
        self.assertEqual(sent["deferral"]["cbs_percent"], 3)
        self.assertEqual(sent["presumed_credit"], "01")
        self.assertNotIn("movable_goods", sent)

    def test_an_nfe_group_goes_out_as_before(self):
        ibs = IbsCbs(cst="000", classification="000001", rate_state=0.1)

        sent = self.body(document_type=DocumentType.NFSE, items=[service(ibs_cbs=ibs)])[
            "items"
        ][0]["product"]["br"]["ibs_cbs"]

        self.assertEqual(
            sent, {"cst": "000", "classification": "000001", "rate_state": 0.1}
        )

    def test_shapes_are_refused(self):
        for build in (
            lambda: IbsCbs(cst="000", classification="000001", presumed_credit="1"),
            lambda: IbsCbs(cst="000", classification="000001", referenced_nfse=["1"]),
            lambda: IbsCbs(cst="000", classification="000001", movable_goods=[]),
            lambda: IbsCbsRecipient(name="x", phone="12"),
            lambda: IbsCbsRecipient(name="x", no_nif_reason="3"),
        ):
            with self.subTest():
                with self.assertRaises(ValidationError):
                    build()


class TestLineAndAddressShapes(unittest.TestCase):
    def test_line_fields_refuse_bad_shapes(self):
        for field, value in (
            ("municipal_service_code", "12"),
            ("municipal_service_code", "1234"),
            ("internal_code", "has space"),
            ("internal_code", "x" * 21),
            ("conditional_discount", Decimal("0")),
            ("conditional_discount", Decimal("1.234")),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValidationError):
                    service(**{field: value})

    def test_address_foreign_fields_refuse_bad_shapes(self):
        for field, value in (
            ("country_iso2", "usa"),
            ("postal_code", ""),
            ("postal_code", "x" * 12),
            ("province", "x" * 61),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    Address(**{field: value})


class TestCatalogAndCompany(unittest.TestCase):
    def sent(self, call, client):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, {})
            call(client)
        return request.call_args

    def test_a_service_item_carries_the_codes(self):
        items = Items(base_url="https://sdk.test", api_key="k")

        args, kwargs = self.sent(
            lambda c: c.create(
                kind="service",
                description="Consultoria",
                service_code="1.07",
                municipal_service_code="001",
                internal_code="SRV01",
            ),
            items,
        )

        self.assertEqual(kwargs["json"]["municipal_service_code"], "001")
        self.assertEqual(kwargs["json"]["internal_code"], "SRV01")

    def test_an_item_update_clears_and_sets_the_codes(self):
        items = Items(base_url="https://sdk.test", api_key="k")

        _, kwargs = self.sent(
            lambda c: c.update("abc", municipal_service_code=None, internal_code="X1"),
            items,
        )

        self.assertEqual(
            kwargs["json"], {"municipal_service_code": None, "internal_code": "X1"}
        )

    def test_the_company_takes_the_nfse_fiscal_fields(self):
        company = Company(base_url="https://sdk.test", api_key="k")
        fields = {
            "approximate_tax_simples_percent": "3.50",
            "approximate_tax_federal_percent": "13.45",
            "approximate_tax_state_percent": "0",
            "approximate_tax_municipal_percent": "2",
            "municipal_registration": "12345",
            "special_tax_regime": "0",
            "iss_rate": "2.50",
        }

        _, kwargs = self.sent(lambda c: c.update(fiscal_fields=fields), company)

        self.assertEqual(kwargs["json"], {"fiscal_fields": fields})

    def test_a_special_tax_regime_outside_the_set_is_refused(self):
        company = Company(base_url="https://sdk.test", api_key="k")

        with self.assertRaises(ValueError):
            company.update(fiscal_fields={"special_tax_regime": "7"})


NBS_ANSWER = {
    "service_code": "010700",
    "suggestions": [
        {
            "nbs": "115021000",
            "description": "Servicos de TI",
            "operation_indicator": "100301",
            "ibs_cbs_classification": "000001",
            "classification_name": "Padrao",
            "added_later": 1,
        }
    ],
    "source": {"path": "nfse/anexo-viii.csv", "date": "2026-01-01"},
}


class TestNbsSuggestions(unittest.TestCase):
    def call(self, code, payload=None):
        client = FiscalReference(base_url="https://sdk.test", api_key="k")
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, payload or NBS_ANSWER)
            result = client.nbs_suggestions(code)
        return request.call_args, result

    def test_it_gets_the_route_and_types_the_answer(self):
        (args, kwargs), result = self.call("1.07")

        self.assertEqual(args, ("GET", f"{BASE}/service-codes/1.07/nbs"))
        self.assertIsInstance(result, NbsSuggestions)
        self.assertEqual(result.service_code, "010700")
        self.assertEqual(result.suggestions[0].nbs, "115021000")
        self.assertEqual(result.suggestions[0].operation_indicator, "100301")
        self.assertEqual(result.suggestions[0].ibs_cbs_classification, "000001")
        self.assertEqual(result.source.path, "nfse/anexo-viii.csv")

    def test_an_empty_list_is_an_answer(self):
        _, result = self.call(
            "010302", {**NBS_ANSWER, "suggestions": [], "service_code": "010302"}
        )

        self.assertEqual(result.suggestions, [])

    def test_a_code_cannot_leave_its_segment(self):
        client = FiscalReference(base_url="https://sdk.test", api_key="k")

        for code in ("", "..", "."):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    client.nbs_suggestions(code)

        (args, _), _ = self.call("1/07")
        self.assertEqual(args[1], f"{BASE}/service-codes/1%2F07/nbs")

    def test_a_code_over_twelve_characters_is_refused(self):
        client = FiscalReference(base_url="https://sdk.test", api_key="k")

        with self.assertRaises(ValueError):
            client.nbs_suggestions("1" * 13)
