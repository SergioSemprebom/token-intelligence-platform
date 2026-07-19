import pytest

import main


def test_main_inicia_o_menu(monkeypatch: pytest.MonkeyPatch) -> None:
    chamadas: list[bool] = []
    monkeypatch.setattr(main, "iniciar_menu", lambda: chamadas.append(True))

    main.main()

    assert chamadas == [True]
