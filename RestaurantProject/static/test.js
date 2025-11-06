    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Success callback: User granted permission and location is available
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                console.log(`Latitude: ${latitude}, Longitude: ${longitude}`);
                // Use latitude and longitude for your application
            },
            (error) => {
                // Error callback: User denied permission or location could not be retrieved
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        console.log("User denied the request for Geolocation.");
                        break;
                    case error.POSITION_UNAVAILABLE:
                        console.log("Location information is unavailable.");
                        break;
                    case error.TIMEOUT:
                        console.log("The request to get user location timed out.");
                        break;
                    case error.UNKNOWN_ERROR:
                        console.log("An unknown error occurred.");
                        break;
                }
            },
            {
                // Optional: Configuration options for the request
                enableHighAccuracy: true, // Request the best possible results
                timeout: 5000,           // Maximum time (in milliseconds) to wait for a position
                maximumAge: 0            // Don't use cached positions
            }
        );
    }