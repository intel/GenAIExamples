# Code Translation Application

Code translation is the process of converting code written in one programming language to another programming language while maintaining the same functionality. This process is also known as code conversion, source-to-source translation, or transpilation. Code translation is often performed when developers want to take advantage of new programming languages, improve code performance, or maintain legacy systems. Some common examples include translating code from Python to Java, or from JavaScript to TypeScript.

The workflow falls into the following architecture:

![architecture](./assets/img/code_trans_architecture.png)

This Code Translation use case uses Text Generation Inference on Intel Gaudi2 or Intel Xeon Scalable Processor. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products) for more details.

# Deploy Code Translation Service

The Code Translation service can be effortlessly deployed on either Intel Gaudi2 or Intel Xeon Scalable Processor.

## Deploy with Docker

- To deploy Code Translation on Gaudi please refer to the [Gaudi Guide](./docker/gaudi/README.md)

- To deploy Code Translation on Xeon please refer to the [Xeon Guide](./docker/xeon/README.md).

## Deploy with Kubernetes

Please refer to the [Code Translation Kubernetes Guide](./kubernetes/README.md)
