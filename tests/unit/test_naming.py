from state_of_data.naming import normalize_column_name, unique_column_names


def test_normalize_column_name_handles_accents_tuple_labels_and_digits() -> None:
    assert normalize_column_name("('P1_a ', 'Área de Formação')") == "p1_a_area_de_formacao"
    assert normalize_column_name("1.a.1_Faixa idade") == "q_1_a_1_faixa_idade"
    assert normalize_column_name("---") == "unnamed"


def test_unique_column_names_suffixes_collisions() -> None:
    assert unique_column_names(["Área", "area", "ÁREA"]) == ["area", "area_2", "area_3"]
