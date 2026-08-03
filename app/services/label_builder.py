from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LabelBuilder:
    def build(
        self,
        *,
        company: str,
        product: str,
        code: str,
        ean: str,
        qrcode: str,
        price: str,
        description: str,
        size: str = "50x30",
        language: str = "PPLB",
    ) -> bytes:
        size_map = {
            "50x30": "50x30",
            "60x40": "60x40",
            "100x50": "100x50",
        }
        selected_size = size_map.get(size, "50x30")
        if language.upper() == "PPLA":
            return (
                b"^XA\n"
                b"^FO50,50^A0N,30,30^FD"
                + company.encode("utf-8")
                + b"^FS\n"
                + f"^FO50,90^A0N,24,24^FD{product}^FS\n".encode("utf-8")
                + f"^FO50,130^A0N,20,20^FD{code}^FS\n".encode("utf-8")
                + f"^FO50,170^A0N,20,20^FD{ean}^FS\n".encode("utf-8")
                + f"^FO50,210^A0N,20,20^FD{qrcode}^FS\n".encode("utf-8")
                + f"^FO50,250^A0N,24,24^FD{price}^FS\n".encode("utf-8")
                + f"^FO50,290^A0N,18,18^FD{description}^FS\n".encode("utf-8")
                + b"^XZ"
            )
        return (
            b"^XA\n"
            + f"^PW{selected_size.split('x')[0]}^PH{selected_size.split('x')[1]}^FS\n".encode("utf-8")
            + b"^FO20,20^A0N,24,24^FD"
            + company.encode("utf-8")
            + b"^FS\n"
            + f"^FO20,60^A0N,22,22^FD{product}^FS\n".encode("utf-8")
            + f"^FO20,100^A0N,20,20^FD{code}^FS\n".encode("utf-8")
            + f"^FO20,140^A0N,20,20^FD{ean}^FS\n".encode("utf-8")
            + f"^FO20,180^A0N,20,20^FD{qrcode}^FS\n".encode("utf-8")
            + f"^FO20,220^A0N,24,24^FD{price}^FS\n".encode("utf-8")
            + f"^FO20,260^A0N,18,18^FD{description}^FS\n".encode("utf-8")
            + b"^XZ"
        )
