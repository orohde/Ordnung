"""A PDF can claim a page of any size: rendering it never takes more than a set amount of memory."""
from ordnung.textextract import MAX_RENDER_PIXELS, _scale


class Page:
    def __init__(self, width, height):
        self.width, self.height = width, height

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height


def test_render_scale_is_capped():
    a4 = Page(595, 842)
    assert _scale(a4, 300 / 72) == 300 / 72                       # an ordinary page keeps its 300 dpi
    for page in (Page(14400, 14400), Page(200_000, 200_000), Page(1, 10_000_000)):
        s = _scale(page, 300 / 72)
        assert page.width * page.height * s * s <= MAX_RENDER_PIXELS * 1.001
    tall = Page(10, 1_000_000)                                       # a thumbnail of a strip stays small
    s = _scale(tall, 240 / 10, max_side=960)
    assert tall.height * s <= 960.001
