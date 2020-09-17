def pytest_runtest_setup(item):
    # Setup code for testing the Cassia Router Ubuntu Container RESTful API.
    print ("This is a setup!", item)