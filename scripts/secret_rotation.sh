#!/bin/bash

# This script provides a template for automating the rotation of secrets stored in
# Google Cloud Secret Manager. It demonstrates how to add a new secret version
# and disable the old one.

# --- Configuration ---
# The GCP Project ID where the secrets are stored.
PROJECT_ID="$(gcloud config get-value project)"

# The name of the secret to rotate.
SECRET_NAME="" # Example: "SUPABASE_KEY"

# The new value for the secret.
NEW_SECRET_VALUE="" # Example: "new_supabase_key_value"

# --- Functions ---

# Function to display usage information.
usage() {
    echo "Usage: $0 -s <SECRET_NAME> -v <NEW_SECRET_VALUE>"
    echo "  -s, --secret      The name of the secret to rotate (e.g., SUPABASE_KEY)."
    echo "  -v, --value       The new value for the secret."
    echo "  -h, --help        Display this help message."
    exit 1
}

# Function to add a new version to a secret.
add_secret_version() {
    local secret_name="$1"
    local new_value="$2"

    echo "Adding new version to secret: $secret_name..."
    if ! echo -n "$new_value" | gcloud secrets versions add "$secret_name" --data-file=- --project="$PROJECT_ID"; then
        echo "Error: Failed to add new secret version for '$secret_name'." >&2
        exit 1
    fi
    echo "Successfully added new version."
}

# Function to disable all old versions of a secret.
disable_old_versions() {
    local secret_name="$1"

    echo "Fetching old versions of secret: $secret_name..."
    # Get all enabled versions, excluding the latest one (which is the one we just added).
    OLD_VERSIONS=$(gcloud secrets versions list "$secret_name" \
        --project="$PROJECT_ID" \
        --filter="state=ENABLED" \
        --format="get(version)" | tail -n +2)

    if [ -z "$OLD_VERSIONS" ]; then
        echo "No old versions to disable."
        return
    fi

    for version in $OLD_VERSIONS; do
        echo "Disabling old version: $version..."
        if ! gcloud secrets versions disable "$version" --secret="$secret_name" --project="$PROJECT_ID"; then
            echo "Warning: Failed to disable version $version for secret '$secret_name'. Manual cleanup may be required." >&2
        else
            echo "Disabled version $version."
        fi
    done
}

# --- Main Execution ---

# Parse command-line arguments.
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -s|--secret)
            SECRET_NAME="$2"
            shift
            shift
            ;;
        -v|--value)
            NEW_SECRET_VALUE="$2"
            shift
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate input.
if [ -z "$SECRET_NAME" ] || [ -z "$NEW_SECRET_VALUE" ]; then
    echo "Error: Secret name and new value are required." >&2
    usage
fi

# Confirm with the user before proceeding.
read -p "This will rotate the secret '$SECRET_NAME' in project '$PROJECT_ID'. Are you sure? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
_then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

# Perform the rotation.
echo "--- Starting Secret Rotation ---"
add_secret_version "$SECRET_NAME" "$NEW_SECRET_VALUE"
disable_old_versions "$SECRET_NAME"
echo "--- Secret Rotation Complete ---"
