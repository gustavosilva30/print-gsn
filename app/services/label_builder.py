from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LabelBuilder:
    """Build thermal label payloads for Argox (PPLA / PPLB) and compatible engines.

    PPLB on Argox OS-214 Plus is ZPL-II compatible and is the default.
    PPLA uses the classic Argox/Datamax text command set.
    """

    dpi: int = 203

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
        darkness: int = 10,
        speed: int = 3,
    ) -> bytes:
        width_mm, height_mm = self._parse_size(size)
        lang = (language or "PPLB").upper()
        if lang in {"PT-BR", "PT", "BR", "EN"}:
            lang = "PPLB"
        if lang == "PPLA":
            return self._build_ppla(
                company=company,
                product=product,
                code=code,
                ean=ean,
                qrcode=qrcode,
                price=price,
                description=description,
                width_mm=width_mm,
                height_mm=height_mm,
                darkness=darkness,
                speed=speed,
            )
        return self._build_pplb(
            company=company,
            product=product,
            code=code,
            ean=ean,
            qrcode=qrcode,
            price=price,
            description=description,
            width_mm=width_mm,
            height_mm=height_mm,
            darkness=darkness,
            speed=speed,
        )

    def _build_pplb(
        self,
        *,
        company: str,
        product: str,
        code: str,
        ean: str,
        qrcode: str,
        price: str,
        description: str,
        width_mm: int,
        height_mm: int,
        darkness: int,
        speed: int,
    ) -> bytes:
        width_dots = self._mm_to_dots(width_mm)
        height_dots = self._mm_to_dots(height_mm)
        safe = self._sanitize
        lines = [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            f"^PR{speed}",
            f"^MD{darkness}",
            f"^FO20,15^A0N,24,24^FD{safe(company)}^FS",
            f"^FO20,45^A0N,22,22^FD{safe(product)}^FS",
            f"^FO20,75^A0N,20,20^FD{safe(code)}^FS",
            f"^FO20,105^A0N,18,18^FD{safe(ean)}^FS",
            f"^FO20,135^A0N,24,24^FD{safe(price)}^FS",
            f"^FO20,165^A0N,16,16^FD{safe(description)}^FS",
        ]
        if ean:
            lines.append(f"^FO20,195^BY2^BCN,50,Y,N,N^FD{safe(ean)}^FS")
        if qrcode:
            lines.append(f"^FO{max(width_dots - 120, 20)},15^BQN,2,4^FDQA,{safe(qrcode)}^FS")
        lines.append("^XZ")
        return "\n".join(lines).encode("utf-8")

    def _build_ppla(
        self,
        *,
        company: str,
        product: str,
        code: str,
        ean: str,
        qrcode: str,
        price: str,
        description: str,
        width_mm: int,
        height_mm: int,
        darkness: int,
        speed: int,
    ) -> bytes:
        safe = self._sanitize
        width_dots = self._mm_to_dots(width_mm)
        height_dots = self._mm_to_dots(height_mm)
        lines = [
            "I8,A,001",
            f"Q{height_dots:04d},024",
            f"q{width_dots}",
            f"S{speed}",
            f"D{darkness}",
            "ZT",
            f'A30,20,0,3,1,1,N,"{safe(company)}"',
            f'A30,55,0,2,1,1,N,"{safe(product)}"',
            f'A30,85,0,2,1,1,N,"{safe(code)}"',
            f'A30,115,0,2,1,1,N,"{safe(ean)}"',
            f'A30,145,0,3,1,1,N,"{safe(price)}"',
            f'A30,180,0,1,1,1,N,"{safe(description)}"',
        ]
        if ean:
            lines.append(f'B30,210,0,1,2,2,50,B,"{safe(ean)}"')
        lines.append("P1")
        return "\n".join(lines).encode("utf-8")


    def build_estoque_crm(
        self,
        *,
        sku: str,
        nome: str,
        localizacao: str = "",
        condicao: str = "Usado",
        marca: str = "",
        modelo: str = "",
        width_mm: int = 50,
        height_mm: int = 25,
    ) -> bytes:
        """Template alinhado ao CRM mobile-estoque (Argox OS-214 Plus, 50x25mm).

        Formato clássico Argox (comandos n/q/Q/B/A/P) usado em raw_print_server.py.
        """
        width_dots = self._mm_to_dots(width_mm)
        height_dots = self._mm_to_dots(height_mm)
        sku_s = self._sanitize(sku)[:32]
        nome_s = self._sanitize(nome)[:30]
        local_s = self._sanitize(localizacao)[:12]
        cond_s = self._sanitize(condicao)[:12]
        compat = ""
        if marca or modelo:
            info = self._sanitize(f"{marca} {modelo}".strip())[:28]
            compat = f'A 10,145,0,2,1,1,N,"{info}"\n'
        pplb = (
            f"n\n"
            f"q {width_dots}\n"
            f"Q {height_dots},26\n"
            f'B 10,8,0,1,2,5,70,B,"{sku_s}"\n'
            f'A 10,88,0,2,1,1,N,"SKU: {sku_s}"\n'
            f'A 10,108,0,2,1,1,N,"{nome_s}"\n'
            f'A 10,128,0,2,1,1,N,"Loc: {local_s} | {cond_s}"\n'
            f"{compat}"
            f"P 1\n"
        )
        return pplb.encode("ascii", errors="replace")

    def _parse_size(self, size: str) -> tuple[int, int]:
        size_map = {
            "50x30": (50, 30),
            "60x40": (60, 40),
            "80x50": (80, 50),
            "100x50": (100, 50),
            "100x80": (100, 80),
        }
        if size in size_map:
            return size_map[size]
        if "x" in size:
            parts = size.lower().split("x", 1)
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                pass
        return 50, 30

    def _mm_to_dots(self, mm: float) -> int:
        return max(1, int(round(mm * self.dpi / 25.4)))

    @staticmethod
    def _sanitize(value: str) -> str:
        # Avoid breaking command syntax with quotes/newlines
        return (
            str(value or "")
            .replace('"', "'")
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("^", " ")
        )
