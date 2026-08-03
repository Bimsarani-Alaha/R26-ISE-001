1.create a virtual environment - python -m venv venv     
                                                                                                               

2.activate environment - venv\Scripts\activate

3.install requirements - pip install -r requirements.txt   

4.version check - python -c "import tensorflow as tf; import keras; print(f'TensorFlow: {tf.__version__}, Keras: {keras.__version__}')"
[must installed-TensorFlow: 2.20.0, Keras: 3.15.1]

5.run backend - python app.py