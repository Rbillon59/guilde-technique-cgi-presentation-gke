# GKE
Google platform managed Kubernetes Clusters


# Workshop

First of all you need to create a GCP project and update __GCP_PROJECT in the files with the project id

## 1. Create a Kubernetes cluster

With the console
 - Go to Kubernetes Engine Tab
 - Cluster --> Create
	 - Name -->  gke-cgi
	 - Zone --> europe-west2-a
	 - Go to advanced option and check
		 - Auto scaling (2 node, min node 1, max node 3)
		 - Preemptible
	- Let the other options as default

or with gcloud command line :

    gcloud beta container --project "__GCP_PROJECT" clusters create "gke-cgi" --zone "europe-west2-a" --no-enable-basic-auth --cluster-version "1.13.11-gke.14" --machine-type "n1-standard-1" --image-type "COS" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --num-nodes "2" --enable-cloud-logging --enable-cloud-monitoring --enable-ip-alias --network "projects/gke-cgi/global/networks/default" --subnetwork "projects/gke-cgi/regions/europe-west2/subnetworks/default" --default-max-pods-per-node "110" --enable-autoscaling --min-nodes "1" --max-nodes "3" --addons HorizontalPodAutoscaling,HttpLoadBalancing --enable-autoupgrade --enable-autorepair

or with terraform :

You need a service account to do this. Go to Cloud IAM and service account, create one with the "Kubernetes Cluster Administrator" role. Generate
a json key and put it at the root of the project and name it `account.json`

Then at the root of the project (and with terraform installed). 

    terraform plan
    terraform apply


## 2. CI/CD on GKE with Cloudbuild

### Push the code to a repository :

The simpler would be to push it to Google source repositories (don't forget to add ssh key to source repositories for your account)

    git clone git@github.com:Rbillon59/guilde-technique-cgi-presentation-gke.git
    cd guilde-technique-cgi-presentation-gke
    rm -rf .git
    git init
    git remote add google ssh://your_account@source.developers.google.com:2022/p/__GCP_PROJECT/r/REPO_NAME

- If you fork it on Github / Bitbucket, you can do a mirroring of the repo in source repositories

You need to update the Cloud Build service account as well so it can deploy to the cluster. 

In IAM, locate the cloud build service account and add it a role called "Kubernetes Cluster Administrator" to grant it the right to manage it and another role called "Object storage creator".

/ ! \ Replace the __REPO_NAME in files with the name of your newly created repository

Create a GCS Bucket named : gke-cgi-cloud-build (left other parameters as default)

#### For the master branch :

Go to the console (https://console.cloud.google.com/cloud-build/)
- Triggers
	- Create trigger
		- Name : master
		- Trigger type : Branch
		- Regex : ^master$ (it means only master branch)
		- Tick "cloud build configuration file"
			- cloudbuild.yaml
		- Save

Now each time you will push code to master / merge into master, the cloud build with trigger the following steps :
- Docker build (The docker file)
- Docker push to Google container registry
- Update the Kubernetes deployment (on the already provisionned Kubernetes Cluster named gke-cgi)


#### For the feature branch
Create another trigger :
- Name : Ephemeral
- Trigger type : Branch
-  Regex : ^master$
	- Tick inverted regex (it means all branch except master)
- Tick "cloud build configuration file"
	- ephemeral_env/cloudbuild-ephemeral.yaml
- Save

Now each time you will push a branch / code into a branch other than master, the cloud build with trigger the following steps :
- Docker build (The docker file)
- Docker push to Google container registry
- Create a new GKE cluster named with the name of the branch (beware of the typo, i.e avoid /) with terraform and store the tfstate file and tflock (files to keep track of the status of the infra) into a GCS Bucket.
- Deploy the kubernetes deployment with the application of the current branch on 2 pods with one Load Balancer
- Wait for the load balancer to be provisioned
- Curl a request to the IP of the load balancer (the test part in fact.. you can put any test you want here, like cucumber, postman, gerkhin, whatever..)

But now we have a cluster running for nothing. So the solution is to destroy it with terraform.

Return to Cloud Build in the console and create a new trigger :
- Name : terraform-destroy
- Trigger type : Branch
- Regex : .*
	- Tick inverted ( means no branch at all)
- Cloud build configuration file :
	- ephemeral_env/destroy.yaml
- Save
- And switch state from Enable to Disable

This cloud build trigger will destroy an environement based on a branch name with terraform

Go to Cloud Function (https://console.cloud.google.com/functions/) and create a new one :
- Name : terraform-destroy
- Memory : 128Mo
- Trigger : Cloud Pub/Sub on cloud build 
- Environment : Python 3.7
	- And copy paste the code from the file cloudfunction.py
- Function to execute : 
	- hello_pubsub (i kept the default one..)

Now each time the cloud build trigger a build, a message is send to the pub/sub queue and will trigger the cloud function. If the branch is not master, no matter the result of the build (success or fail) and the step is not terraform (without this condition, it will loop destroying because it trigger a build itself), the cloud function will trigger by an API call the terraform-destroy cloud build.

Now you have a CI/CD provisioning ephemeral environments at each push / branch making tests and then destroying it.

## 3. Horizontal Scaling

On the deployment.yaml there is a block defining autoscaling ressource :

    apiVersion: autoscaling/v1
	kind: HorizontalPodAutoscaler
	metadata:
		name: hello-cgi
	spec:
		maxReplicas: 10
		minReplicas: 1
		scaleTargetRef:
			apiVersion: extensions/v1beta1
			kind: Deployment
			name: hello-cgi
		targetCPUUtilizationPercentage: 30

And on the cluster creation we have ticked the node autoscaling feature. So lets make it burn.

in your system install apache-bench (ab) (on fedora/centOs `yum/dnf install httpd-tools`, on Ubuntu/Debian `apt install apache2-tools`) on windows .. don't know.

in your command prompt :

    ab -n 1000 -c 10 http://your_loadbalancer_ip/compute

As you can see in the main.py file, the /compute request make a loop of 1 million random power random follow by division. Which is pretty cpu expensive.

So here there will launch 1000 requests with 10 virtual users. Now go on the Kubernetes Engine menu and check the workload, the pod autoscaler will scale the number of pods up to 7 and 3 pods will be unschedulable because the two nodes are full. So GKE will provision a third node and deploy the remaining pods.

You can play with stackdriver monitoring as well during the test to explore available metrics and eventually play with alerting as well

After the end of the bench, your cluster will slowly return to it idle state as defined in your deployment.yml. 2 replicas on 2 nodes
