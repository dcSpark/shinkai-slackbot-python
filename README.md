# Shinkai Slack bot Python integration

How to start?

```bash

# setup `venv` to run stuff 
source venv/bin/activate

# install packages 
pip install -r requirements.txt

# make sure to install shinkai_message_pyo3-0.1.6-cp38-abi3-macosx_11_0_arm64.whl lib which is not available in pip yet
pip install shinkai_message_pyo3-0.1.6-cp38-abi3-macosx_11_0_arm64.whl 

# in case the lib needs to be reinstalled, use --force-reinstall
pip install shinkai_message_pyo3-0.1.6-cp38-abi3-macosx_11_0_arm64.whl --force-reinstall

# to run the service
python main.py

# running tests
pytest test_integration # default testing command
pytest -s test_integration.py # to see logs
pytest -p no:warnings test_integration.py # to hide any warnings (logs won't appear)
```
