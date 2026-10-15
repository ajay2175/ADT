from app.experiments.h1_calibration import validate_calibration_file


def test_ten_ayurveda_calibration_cases():
    report = validate_calibration_file()
    assert report["n_cases"] == 10
    assert report["valid"]
