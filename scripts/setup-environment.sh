#! /bin/bash.

echo "***********************Install kubectl******************************"

sudo curl --silent --location -o /usr/local/bin/kubectl \
   https://amazon-eks.s3.us-west-2.amazonaws.com/1.19.6/2021-01-05/bin/linux/amd64/kubectl

sudo chmod +x /usr/local/bin/kubectl


## 2. install eksctl
echo "***********************Lauch EKS cluster******************************"


curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp

sudo mv -v /tmp/eksctl /usr/local/bin
eksctl version


## 2. install eksctl
echo "***********************Install kustomize ******************************"

curl --silent --location --remote-name \
"https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v3.2.3/kustomize_kustomize.v3.2.3_linux_amd64" && \
chmod a+x kustomize_kustomize.v3.2.3_linux_amd64 && \
sudo mv kustomize_kustomize.v3.2.3_linux_amd64 /usr/local/bin/kustomize
