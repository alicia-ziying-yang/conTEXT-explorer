from dash.testing.application_runners import import_app


def test_one(dash_duo):
	app = import_app("app")
	dash_duo.start_server(app)
	dash_duo.wait_for_text_to_equal("#corpus-select-title", "Use an existing corpus", timeout=5)
	
