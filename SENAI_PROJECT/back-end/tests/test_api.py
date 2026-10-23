from datetime import datetime, timedelta, timezone


def _player(name: str, position: str) -> dict:
    return {
        "name": name,
        "position": position,
        "agility": 50,
        "age": 25,
        "pace": 75,
        "shooting": 75,
        "passing": 75,
        "dribbling": 75,
        "defending": 75,
        "physical": 75,
        "potential": 75,
    }


def _future_contract() -> str:
    moment = datetime.now(timezone(timedelta(hours=-3))) + timedelta(days=100)
    return moment.strftime("%Y-%m-%dT%H:%M-03:00")


def _create_team(client, name: str, acronym: str, prefix: str) -> tuple[int, list[int]]:
    club_response = client.post(
        "/api/v1/clubs",
        json={"name": name, "acronym": acronym},
    )
    assert club_response.status_code == 201
    club_id = club_response.json()["id"]
    player_ids = []
    for suffix, position in (
        ("Goleiro", "GOL"),
        ("Zagueiro", "ZAG"),
        ("Lateral", "LAT"),
        ("Meia", "MEI"),
        ("Atacante", "ATA"),
    ):
        response = client.post(
            "/api/v1/players",
            json=_player(f"{prefix} {suffix}", position),
        )
        assert response.status_code == 201, response.text
        player_id = response.json()["id"]
        player_ids.append(player_id)
        bought = client.post(
            f"/api/v1/players/{player_id}/buy",
            json={"club_id": club_id, "loyalty_until": _future_contract()},
        )
        assert bought.status_code == 200, bought.text
        assert bought.json()["fee"] == 2.0
    lineup = client.put(
        f"/api/v1/clubs/{club_id}/lineup",
        json={"formation": "2-1-1", "player_ids": player_ids},
    )
    assert lineup.status_code == 200, lineup.text
    return club_id, player_ids


def test_complete_league_flow_and_snapshot_history(client):
    home_id, home_players = _create_team(client, "Águias FC", "AGU", "Rui")
    away_id, _ = _create_team(client, "Delta FC", "DEL", "Ivo")

    match_response = client.post(
        "/api/v1/matches",
        json={"home_club_id": home_id, "away_club_id": away_id},
    )
    assert match_response.status_code == 201, match_response.text
    played = match_response.json()
    assert len(played["duels"]) == 6
    assert [duel["order"] for duel in played["duels"]] == [1, 2, 3, 4, 5, 6]
    assert played["result"] == "EMPATE"

    sale = client.post(f"/api/v1/players/{home_players[-1]}/sell")
    assert sale.status_code == 200, sale.text
    assert sale.json()["penalty"] == 4.0
    assert sale.json()["contract_status"] == "RESCINDIDO"

    lineup = client.get(f"/api/v1/clubs/{home_id}/lineup").json()
    assert lineup["complete"] is False
    assert len(lineup["players"]) == 4

    history = client.get(f"/api/v1/clubs/{home_id}/transactions").json()
    assert len(history["data"]) == 6
    assert history["summary"]["total_spent"] == 210.0
    assert history["summary"]["total_received"] == 36.0
    csv_response = client.get(f"/api/v1/clubs/{home_id}/transactions/export?type=VENDA")
    assert csv_response.status_code == 200
    assert csv_response.text.splitlines()[0] == (
        "data_hora;tipo;jogador;valor;taxa_ou_comissao;multa;lucro;variacao_caixa"
    )
    assert csv_response.content.endswith(b"\n")

    old_match = client.get(f"/api/v1/matches/{played['id']}").json()
    assert len(old_match["duels"]) == 6
    assert old_match["home"]["goals"] == 0
    standings = client.get("/api/v1/standings").json()
    assert len(standings) == 2
    assert all(item["draws"] == 1 for item in standings)


def test_invalid_values_are_400_and_business_conflicts_are_409(client):
    response = client.post(
        "/api/v1/players",
        json={**_player("João Silva", "MEI"), "age": "25"},
    )
    assert response.status_code == 400
    assert "message" in response.json()

    player = client.post(
        "/api/v1/players",
        json=_player("João Silva", "MEI"),
    ).json()
    assert (
        client.patch(
            f"/api/v1/players/{player['id']}/condition",
            json={"condition": "DOENTE"},
        ).status_code
        == 200
    )
    response = client.patch(
        f"/api/v1/players/{player['id']}/condition",
        json={"condition": "APTO"},
    )
    assert response.status_code == 409
    assert "message" in response.json()
