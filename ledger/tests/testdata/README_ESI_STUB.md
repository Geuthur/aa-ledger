# ESI OpenAPI Stub System

Ein eigenständiges Stub-System für ESI OpenAPI-Clients, das für Tests verwendet werden kann, um vordefinierte Testdaten zurückzugeben, ohne echte API-Aufrufe zu machen.

## Übersicht

**Wichtig:** Dieses Stub-System gibt Objekte mit Attributen zurück (wie OpenAPI 3 Clients), **nicht** Dictionaries!

```python
# ✓ Richtig - Attributzugriff
result.total_sp
result.skills[0].skill_id

# ✗ Falsch - Dictionary-Zugriff
result["total_sp"]  # AttributeError!
result["skills"][0]["skill_id"]  # AttributeError!
```

Dieses System bietet vier Hauptklassen:

- **`EsiEndpoint`**: Definition eines ESI-Endpoints mit optionalem Side-Effect
- **`EsiOperationStub`**: Simuliert eine ESI-Operation und stellt `result()` und `results()` Methoden bereit
- **`EsiCategoryStub`**: Repräsentiert eine ESI-Kategorie (z.B. Skills, Character, Wallet)
- **`EsiClientStub`**: Der Haupt-Client, der `ESIClientProvider.client` nachahmt

## Verwendung

### Endpoints sind erforderlich!

**Wichtig:** Die `endpoints` Liste ist IMMER erforderlich! Sie definiert, welche ESI-Methoden verfügbar sind.

```python
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)

# Endpoints definieren (ERFORDERLICH!)
endpoints = [
    EsiEndpoint("Character", "GetCharactersCharacterId", "character_id"),
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
]

test_data = {
    "Character": {"GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}},
    "Skills": {"GetCharactersCharacterIdSkills": {"total_sp": 50000000, "skills": []}},
}

# Stub erstellen - endpoints MÜSSEN angegeben werden
stub = create_esi_client_stub(test_data, endpoints=endpoints)

# Nur registrierte Endpoints sind verfügbar
operation = stub.Character.GetCharactersCharacterId(character_id=12345)
result = operation.result()
```

Ohne `endpoints` wird ein `ValueError` geworfen:

```python
# Dies wirft ValueError!
stub = create_esi_client_stub(test_data)  # ❌ Fehler: endpoints fehlt
```

### Grundlegende Verwendung

```python
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)

# Testdaten definieren
test_data = {
    "Skills": {
        "GetCharactersCharacterIdSkills": {
            "skills": [
                {"skill_id": 12345, "trained_skill_level": 5, "active_skill_level": 5}
            ],
            "total_sp": 50000000,
            "unallocated_sp": 100000,
        }
    }
}

# Endpoints definieren (ERFORDERLICH!)
endpoints = [
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
]

# Stub erstellen
stub = create_esi_client_stub(test_data, endpoints=endpoints)

# Verwenden wie echten ESI-Client
operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
result = operation.result()

# Ergebnis ist ein Objekt mit Attributen (wie OpenAPI 3)
print(result.total_sp)  # 50000000
print(result.skills[0].skill_id)  # 12345
```

### Mit `result()` für einzelne Ergebnisse

```python
# Für Methoden, die ein einzelnes Objekt zurückgeben
operation = stub.Character.GetCharactersCharacterId(character_id=12345)
data = operation.result()
```

### Mit `results()` für Listen

```python
# Für Methoden, die eine Liste zurückgeben (paginierte Daten)
operation = stub.Skills.GetCharactersCharacterIdSkillqueue(character_id=12345)
data_list = operation.results()
```

### Mit Mock/Patch in Tests

```python
from unittest.mock import patch, PropertyMock
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)


@patch("taxsystem.providers.esi")
def test_something(self, mock_esi):
    # Endpoints definieren
    endpoints = [
        EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
    ]

    # Stub erstellen
    stub = create_esi_client_stub(test_data, endpoints=endpoints)

    # ESI-Client durch Stub ersetzen (client ist eine Property)
    type(mock_esi).client = PropertyMock(return_value=stub)

    # Ihre Testlogik hier...
```

### Dynamische Testdaten

Sie können auch Callables verwenden, um dynamische Testdaten basierend auf Eingabeparametern zu generieren:

```python
def dynamic_skills(character_id, **kwargs):
    return {"total_sp": character_id * 1000, "skills": [], "unallocated_sp": 0}


test_data = {"Skills": {"GetCharactersCharacterIdSkills": dynamic_skills}}

# Endpoints definieren
endpoints = [
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
]

stub = create_esi_client_stub(test_data, endpoints=endpoints)
operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=100)
result = operation.result()
# result.total_sp wird 100000 sein
```

### Exceptions/Side-Effects simulieren

Sie können ESI-Exceptions über Endpoint-Definitionen simulieren:

```python
from esi.exceptions import HTTPNotModified, HTTPClientError, HTTPServerError
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)

# Endpoints mit Side-Effects definieren
endpoints = [
    EsiEndpoint(
        "Character",
        "GetCharactersCharacterId",
        "character_id",
        side_effect=HTTPNotModified(304, {}),
    ),
    EsiEndpoint(
        "Skills",
        "GetCharactersCharacterIdSkills",
        "character_id",
        side_effect=HTTPClientError(404, {}, b"Not Found"),
    ),
]

# Testdaten (werden nur zurückgegeben, wenn kein side_effect auftritt)
test_data = {
    "Character": {"GetCharactersCharacterId": {"character_id": 12345, "name": "Test"}},
    "Skills": {"GetCharactersCharacterIdSkills": {"total_sp": 0, "skills": []}},
}

stub = create_esi_client_stub(test_data, endpoints=endpoints)

# Wirft HTTPNotModified
try:
    operation = stub.Character.GetCharactersCharacterId(character_id=12345)
    result = operation.result()
except HTTPNotModified:
    print("Cached data is still valid!")

# Wirft HTTPClientError
try:
    operation = stub.Skills.GetCharactersCharacterIdSkills(character_id=12345)
    result = operation.result()
except HTTPClientError:
    print("Client error occurred!")
```

#### Unterstützte Exceptions:

- `HTTPNotModified` (304) - Cached data ist noch gültig
- `HTTPClientError` (4xx) - Client-Fehler (z.B. 404, 403)
- `HTTPServerError` (5xx) - Server-Fehler
- `OSError` - Netzwerk-/Verbindungsfehler
- Jede andere Python Exception

#### Ohne Side-Effect:

Endpoints ohne `side_effect` geben normale Testdaten zurück:

```python
endpoints = [
    EsiEndpoint(
        "Character",
        "GetCharactersCharacterId",
        "character_id",
        # Kein side_effect - gibt Testdaten zurück
    ),
]

test_data = {
    "Character": {
        "GetCharactersCharacterId": {"character_id": 12345, "name": "Test Pilot"}
    }
}

stub = create_esi_client_stub(test_data, endpoints=endpoints)
operation = stub.Character.GetCharactersCharacterId(character_id=12345)
result = operation.result()
print(result.name)  # "Test Pilot"
```

### Mit return_response Parameter

```python
# Tuple aus (data, response) erhalten
operation = stub.Character.GetCharactersCharacterId(character_id=12345)
data, response = operation.result(return_response=True)

print(data.character_id)  # 12345678
print(response.status_code)  # 200
print(response.headers)  # {}
```

## Struktur der Testdaten

Die Testdaten sollten folgende Struktur haben:

```python
{
    "KategorieName": {
        "MethodenName": {...},  # Dict oder Liste von Dicts
        "AndereMethode": {...},
    },
    "AndereKategorie": {"MethodenName": {...}},
}
```

### Beispiel:

```python
{
    "Skills": {
        "GetCharactersCharacterIdSkills": {"skills": [...], "total_sp": 50000000},
        "GetCharactersCharacterIdSkillqueue": [
            {"skill_id": 111, "queue_position": 0},
            {"skill_id": 222, "queue_position": 1},
        ],
    },
    "Character": {
        "GetCharactersCharacterId": {"character_id": 12345, "name": "Test Pilot"}
    },
}
```

### Auswahl von Methodendaten per Parameterwert

Die Stub-Implementierung unterstützt auch Mapping-Objekte, bei denen die Werte nach
eingehenden Parametern ausgewählt werden. Wenn für eine Methode statt eines einfachen
Objekts ein Dictionary angegeben wird, versucht der Stub, einen passenden Eintrag
zu finden, dessen Schlüssel dem Parameterwert (als String oder Integer) entspricht.

Beispiel: Wenn der Endpoint `character_id` als Parameter verwendet wird, kann das
Testdaten-Format so aussehen:

```python
{
    "Character": {
        "GetCharactersCharacterId": {
            "12345": {"character_id": 12345, "name": "Alpha"},
            "67890": {"character_id": 67890, "name": "Beta"},
        }
    }
}
```

Aufruf mit `character_id=12345` liefert dann automatisch den Eintrag für den Schlüssel
`"12345"`. Numerische Schlüssel werden ebenfalls unterstützt (z. B. `12345` statt
`"12345"`).

Wenn das Mapping nur einen Eintrag enthält, wird dieser Eintrag als Fallback immer
zurückgegeben (praktisch für einfache Defaults oder wenn nur ein Testfall benötigt wird).

### Sequentielle Side-Effects

Endpoints können als `side_effect` eine Exception oder eine Liste von Exceptions/Werten
haben. Wird eine Liste übergeben, werden die Einträge sequenziell verbraucht (nützlich
für Tests, die mehrere Aufrufe mit unterschiedlichen Ergebnissen simulieren).

### Automatisches Laden aus JSON

`create_esi_client_stub(test_data_config=None, endpoints=...)` lädt automatisch
Testdaten aus der Datei `esi_test_data.json` im gleichen Verzeichnis, wenn
`test_data_config` nicht übergeben wird. Die `endpoints`-Liste bleibt weiterhin
erforderlich und wird validiert.

### Mit Endpoints und Side-Effects:

```python
from esi.exceptions import HTTPNotModified, HTTPClientError
from taxsystem.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)

# Endpoints definieren
endpoints = [
    EsiEndpoint(
        "Skills",
        "GetCharactersCharacterIdSkills",
        "character_id",
        side_effect=HTTPNotModified(304, {}),
    ),
    EsiEndpoint(
        "Skills",
        "GetCharactersCharacterIdSkillqueue",
        "character_id",
        # Kein side_effect
    ),
]

# Testdaten
test_data = {
    "Skills": {
        "GetCharactersCharacterIdSkills": {"total_sp": 0, "skills": []},
        "GetCharactersCharacterIdSkillqueue": [{"skill_id": 123}],
    }
}

# Stub erstellen
stub = create_esi_client_stub(test_data, endpoints=endpoints)
```

````

## Unterschied zwischen `result()` und `results()`

- **`result()`**: Gibt die Testdaten als Objekt zurück (für einzelne Ergebnisse)
  - Dictionaries werden in SimpleNamespace-Objekte konvertiert
  - Zugriff über Attribute: `result.total_sp`
- **`results()`**:
  - Wenn Testdaten bereits eine Liste sind, wird sie als Liste von Objekten zurückgegeben
  - Wenn Testdaten ein einzelnes Objekt sind, wird es in eine Liste gewrappt
  - Zugriff: `results[0].skill_id`

## Parameter

Beide Methoden akzeptieren die gleichen Parameter wie die echten ESI-Operationen:

```python
operation.result(
    use_etag=True, return_response=False, force_refresh=False, use_cache=True
)

operation.results(
    use_etag=True, return_response=False, force_refresh=False, use_cache=True
)
```

Diese Parameter werden im Stub ignoriert, aber akzeptiert, um die echte API-Signatur zu matchen.

## Beispiele

Siehe `test_esi_stub.py` für vollständige Beispiele der Verwendung, einschließlich:

- Grundlegende `result()` und `results()` Aufrufe
- Verwendung mit `return_response=True`
- Simulation von Exceptions (HTTPNotModified, HTTPClientError, etc.)
- Sequentielle Side-Effects
- Dynamische Testdaten
- Integration mit Mock/Patch

## Datenkonvertierung

Alle Testdaten (JSON/Dict) werden automatisch in Objekte mit Attributen konvertiert:

```python
# Testdaten als Dict
test_data = {
    "Skills": {
        "GetCharactersCharacterIdSkills": {
            "total_sp": 50000000,
            "skills": [{"skill_id": 123}],
        }
    }
}

# Wird zu Objekten konvertiert
result = operation.result()
result.total_sp  # 50000000 (Attributzugriff!)
result.skills[0].skill_id  # 123 (Attributzugriff!)
```
````
