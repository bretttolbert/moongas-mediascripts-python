from mediascripts.rename.rename_album_files import update_filename


def test_update_filename_applies_filename_cleanup_rules() -> None:
    filename = "03 - Lil Wayne - MegaMan [Official Music Video] 🔄.mp3"

    assert update_filename(filename, "Lil Wayne") == "03 - MegaMan.mp3"


def test_update_filename_normalizes_artist_and_featured_artist() -> None:
    filename = "04 - Jay‐Z feat. Rick Ross - FuckWithMeYouKnowIGotIt.mp3"

    assert (
        update_filename(filename, "Jay-Z")
        == "04 - Jay-Z ft Rick Ross - FuckWithMeYouKnowIGotIt.mp3"
    )
