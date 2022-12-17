#! /bin/bash
echo '****************remove existing manifist files!**************************************'
#rm -r kubeflow-manifests

echo '****************deploying eks cluster **************************************'
eksctl create cluster -f Scripts/kubeflow.yaml

echo '****************downloading the manifist files!**************************************'

export KUBEFLOW_RELEASE_VERSION=v1.4.1
export AWS_RELEASE_VERSION=v1.4.1-aws-b1.0.0
git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests
git checkout ${AWS_RELEASE_VERSION}
git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream

echo '****************downloading the manifist files completed!**************************************'




echo '****************installing kubeflow using kustomization**************************************'
while ! kustomize build docs/deployment/vanilla | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done

echo '****************making sure everything is installed**************************************'
kubectl get pods -n cert-manager
kubectl get pods -n istio-system
kubectl get pods -n auth
kubectl get pods -n knative-eventing
kubectl get pods -n knative-serving
kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-user-example-com


echo '****************port forwarding**************************************'

# cto-nbi-kubeflow
