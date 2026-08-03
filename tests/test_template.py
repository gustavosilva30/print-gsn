from app.domain.template import Template, TemplateElement


def test_template_render_returns_bytes():
    template = Template(name="peca", elements=[TemplateElement(type="text", text="Hello")])
    payload = {"codigo": "1"}
    assert template.render(payload) == b"template-render"
