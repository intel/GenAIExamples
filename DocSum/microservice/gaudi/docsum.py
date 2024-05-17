# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import os

from comps import MicroService, ServiceOrchestrator, ServiceType

SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")

class DocSumService:
    def __init__(self, port=8000):
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        llm = MicroService(
            name="llm", 
            host=SERVICE_HOST_IP,
            port=9000, 
            endpoint="/v1/chat/docsum",
            use_remote_service=True,
            service_type=ServiceType.LLM,
            )
        self.megaservice.add(llm)

    def schedule(self):
        self.megaservice.schedule(
            initial_inputs={"text":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}
        )
        result_dict = self.megaservice.result_dict
        print(result_dict)


if __name__ == "__main__":
    docsum = DocSumService(port=9001)
    docsum.add_remote_service()
    asyncio.run(docsum.schedule())
