import numpy as np

from crystal_agent.ui.lens import GlassPanelRenderer


def test_glass_panel_keeps_desktop_colors_untinted_interior():
    frame = np.empty((100, 140, 3), dtype=np.uint8)
    frame[:] = (40, 100, 180)
    renderer = GlassPanelRenderer()
    renderer.configure(0, 0, 140, 100)

    image = renderer.render(frame)

    assert tuple(image[50, 70, :3]) == (40, 100, 180)
    assert image[50, 70, 3] == 255
    assert image[0, 0, 3] == 0
