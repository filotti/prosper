# Prosper Auto-Investor

## Introduction

This application is designed to automate the investment process for listings on Prosper. It retrieves your account
balance, and if it's over the minimum investment amount, it checks listings matching your criteria and automatically
places bids on them.

## Prerequisites

1. A Google Cloud Platform (GCP) Project
2. A Prosper investor account

This application runs on the GCP Cloud Functions platform and uses Secrets Manager to store sensitive information. It's 
triggered by a Cloud Scheduler job that sends a message to a Pub/Sub topic, which in turn starts the Cloud Function.

## GCP Components Used

This application integrates multiple components from Google Cloud Platform (GCP) for seamless automation and secure data 
management.

### Google Secrets Manager
Google Secrets Manager allows us to securely and conveniently manage sensitive data like the credentials used to call 
the Prosper API. 

**Features Utilized:**

* Secure storage of secrets.
* Versioning of secrets, allowing us to keep a history and roll back if needed.
* Access control, ensuring only authorized entities can fetch the secrets.

### Cloud Functions

The core logic of the auto-investor is encapsulated in a Cloud Function. Cloud Functions are lightweight, serverless 
compute solutions that allow you to run your code without provisioning or managing servers.

**Features Utilized:**

* Serverless execution: Only worry about the code, not the infrastructure.
* Event-driven: Our function is designed to be triggered by a specific event - a message on a Pub/Sub topic that is
pushed by Cloud Scheduler.
* Pay only when your code runs: You're only charged for the time your code is running. For this use case, the free tier
is sufficient.

### Cloud Scheduler

Cloud Scheduler is a managed cron job service. In the context of this application, it's responsible for triggering the 
Cloud Function at defined intervals. By setting up Cloud Scheduler, the investment process can be automated to run, for example, every day at a specific time.

**Features Utilized:**

* Recurring scheduling: Specify how often the job should run (e.g., every day at 9 AM).
* Targeted payloads: Send specific data to the Cloud Function if necessary. 
* Standard Cron format: Familiar syntax for defining the schedule, with support for standard Linux cron expressions.

### Pub/Sub

Google Cloud Pub/Sub facilitates real-time messaging between applications. In this application, Cloud Scheduler pushes a message to a Pub/Sub topic, which in turn triggers the Cloud Function.

**Features Utilized:**

* Decoupling of services: Cloud Scheduler and Cloud Functions interact indirectly, reducing dependencies.
* Scalability: Can handle a vast number of messages, allowing for potential future expansions of the application.

## Setup

Unless you really know what you're doing, I recommend running these commands from Cloud Shell. This will
make sure you're using the correct project and account.

### 1. Clone the repository

```
git clone https://github.com/filotti/prosper.git
cd prosper
```

### 2. Enable the required APIs
```
gcloud services enable secretmanager.googleapis.com cloudfunctions.googleapis.com cloudscheduler.googleapis.com pubsub.googleapis.com cloudbuild.googleapis.com
 ```

### 3. Store the secrets in Secrets Manager

Store the following secrets in Google Secrets Manager:

- `PROSPER_USER`: Your Prosper username.
- `PROSPER_PASSWORD`: Your Prosper password.
- `PROSPER_CLIENT_ID`: Prosper Client ID.
- `PROSPER_CLIENT_SECRET`: Prosper Client Secret.

You need to register your application with Prosper to get these credentials. Go to Settings -> API and your can
generate the Client ID and Client Secret there.

### 4. Create the Pub/Sub topic

```
gcloud pubsub topics create prosper
```

### 5. Create the Cloud Scheduler job

```
gcloud scheduler jobs create pubsub prosper --schedule="0 * * * *" --topic prosper --message-body="{}" --location=us-central1
```

**Note:** The above command will trigger the Cloud Function every hour. You can change the schedule to whatever you 
want by specifying a different cron expression. For example, to trigger the function every day at 9 AM, you would use 
`0 9 * * *`.

Running the Cloud Function every hour will allow you to invest in listings as soon as they become available and you
have enough funds in your account. 

### 6. Set environment variables including the investment amounts and criteria

The Cloud Function requires the following environment variables to be set:

- `GCP_PROJECT`: Your GCP project ID.
- `INVESTMENT_AMOUNT`: The amount you wish to invest per listing.
- `INVESTMENT_CRITERIA`: A JSON string containing the criteria for listings you want to invest in. Example:

    ```json
    {
        "prosper_rating": ["C", "D", "E"],
        "listing_term": ["24", "36"],
        "g218b_max": "0",
        "biddable": "true",
        "sort_by": "percent_funded desc",
        "amount_remaining_min": "25"
    }
    ```

You can find all the available filtering criteria in the 
[Prosper API documentation](https://developers.prosper.com/docs/investor/listings-api/).

Using Cloud Shell, you can set the variables like this:
```
export GCP_PROJECT=$DEVSHELL_PROJECT_ID
export INVESTMENT_AMOUNT=25
export INVESTMENT_CRITERIA='{"prosper_rating":["C","D","E"],"listing_term":["24","36"],"g218b_number_of_delinquent_accounts":"0","biddable":"true","sort_by":"percent_funded desc","amount_remaining_min":"25"}'
```

These criteria will invest in:

- Listings with a Prosper Rating of C, D, or E.
- Listings with a term of 24 or 36 months.
- Listings that had no delinquencies in the last 7 years.
- Listings that are biddable.
- Listings with a remaining biddable amount of at least $25.

And it will invest $25 in each listing.

### 7. Deploy the Cloud Function

Run the following command to deploy the Cloud Function:

```
gcloud functions deploy prosper \
--runtime python311 \
--trigger-topic prosper \
--region us-central1 \
--set-env-vars GCP_PROJECT=$GCP_PROJECT,INVESTMENT_AMOUNT=$INVESTMENT_AMOUNT,INVESTMENT_CRITERIA=$INVESTMENT_CRITERIA \
--source=. \
--docker-registry artifact-registry 
```

### 8. Test the Cloud Function

You can test the Cloud Function by triggering a manual execution in Cloud Scheduler. To do this, go to the Cloud
Scheduler page in the GCP Console, click on the three dots next to the job you created, and select "Force Run".

### 9. Check the logs

You can check the logs for the Cloud Function in the GCP Console. Go to the Cloud Functions page, click on the name of
the function, and then click on the "Logs" tab. You should see a log entry for each listing that was invested in.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* [Prosper](https://www.prosper.com/) for providing the API that makes this possible. However, I should add that 
this tool is not officially affiliated with, endorsed by, or in any way officially connected with Prosper.
