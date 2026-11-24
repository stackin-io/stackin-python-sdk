import os
from datetime import date
from decimal import Decimal

from dotenv import load_dotenv

from stackin import DocumentType, Invoice
from stackin.br import ApproximateTaxes, IssDetails, NfseDetails, Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    result = client.issue(
        document_type=DocumentType.NFSE,
        client_name="Comprador Teste Ltda",
        tax_id="11222333000181",
        recipient_municipal_registration="123456",
        items=[
            Product(
                description="Consultoria em tecnologia",
                unit_price=Decimal("1500.00"),
                service_code="1.07",
                nbs="1.1502.10.00",
                municipal_service_code="001",
                internal_code="CONS01",
                conditional_discount=Decimal("50.00"),
            )
        ],
        nfse=NfseDetails(
            competence_date=date.today(),
            approximate_taxes=ApproximateTaxes(
                federal_percent=Decimal("13.45"),
                state_percent=Decimal("0"),
                municipal_percent=Decimal("2"),
            ),
            iss=IssDetails(rate=Decimal("2.5"), retention="none"),
        ),
    )

    print(result)


if __name__ == "__main__":
    main()
