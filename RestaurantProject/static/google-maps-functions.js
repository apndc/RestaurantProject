
  
    // ----- Calendar -----
    const calendarGrid = document.getElementById('calendarGrid');
    function renderCalendar(view) {
      calendarGrid.innerHTML = '';
      const days = view === 'week' ? 7 : 30;
      for (let i = 1; i <= days; i++) {
        const div = document.createElement('div');
        div.className = 'day';
        div.textContent = `Day ${i}`;
        div.onclick = () => alert(`Events for Day ${i}`);
        calendarGrid.appendChild(div);
      }
    }
    function switchView(view) { renderCalendar(view); }
    renderCalendar('week');

    // ----- Checklist -----
    const taskList = document.getElementById('taskList');
    const storedTasks = JSON.parse(localStorage.getItem('bookitTasks')) || [];
    function renderTasks() {
      taskList.innerHTML = '';
      storedTasks.forEach((task, i) => {
        const li = document.createElement('li');
        li.textContent = task;
        const btn = document.createElement('button');
        btn.textContent = 'X';
        btn.onclick = () => { storedTasks.splice(i, 1); saveTasks(); };
        li.appendChild(btn);
        taskList.appendChild(li);
      });
    }
    function addTask() {
      const input = document.getElementById('newTask');
      if (input.value.trim() !== '') {
        storedTasks.push(input.value.trim());
        input.value = '';
        saveTasks();
      }
    }
    function saveTasks() {
      localStorage.setItem('bookitTasks', JSON.stringify(storedTasks));
      renderTasks();
    }
    renderTasks();

    // ----- Restaurants Modal -----
    function openModal(name, email) {
      document.getElementById('modal').style.display = 'flex';
      document.getElementById('modalName').textContent = name;
      document.getElementById('modalEmail').textContent = email;
    }
    function closeModal() {
      document.getElementById('modal').style.display = 'none';
    }

    // ----- Google Maps + Places -----
    let map, service, infowindow, userMarker;

  async function initMap() {
    // Request needed libraries.
    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    await google.maps.importLibrary("places");

    // Initialize the map.
    map = new Map(document.getElementById("map"), {
        center: { lat: 40.749933, lng: -73.98633 }, // Default to New York City
        zoom: 13,
        mapId: 'DEMO_MAP_ID'
    });

    // Create a marker that will be reused.
    marker = new AdvancedMarkerElement({
        map: map,
    });

    // Get the info panel element.
    infoPanel = document.getElementById('info-content');

    // Create the PlaceAutocompleteElement and append it to the container.
    const placeAutocomplete = new google.maps.places.PlaceAutocompleteElement();
    document.getElementById('autocomplete-container').appendChild(placeAutocomplete);

    // Add the 'gmp-select' listener to handle place selection.
    placeAutocomplete.addEventListener('gmp-select', async ({ placePrediction }) => {
      const place = placePrediction.toPlace();
      await place.fetchFields({ fields: ['displayName', 'formattedAddress', 'location'] });

      // Clear previous info and handle no selection.
      if (!place.location) {
            infoPanel.innerHTML = '<p>No details available for this selection.</p>';
            marker.position = null;
            return;
        }

        // Center the map on the selected place and update the marker.
        map.setCenter(place.location);
        marker.position = place.location;
        marker.title = place.displayName;

        // Update the info panel with the new place details.
        infoPanel.innerHTML = `
            <h3 class="font-bold text-lg">${place.displayName}</h3>
            <p class="mt-2">${place.formattedAddress}</p>
        `;
      });
    }

    initMap();


    function searchVenue() {
      const query = document.getElementById('venueSearch').value;
      if (!query) { alert("Please enter a search term."); return; }

      const request = {
        query: query + " event venues",
        fields: ["name", "geometry", "formatted_address"],
      };

      service = new google.maps.places.PlacesService(map);
      service.textSearch(request, (results, status) => {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
          map.setCenter(results[0].geometry.location);
          results.forEach(place => {
            const marker = new google.maps.Marker({
              map,
              position: place.geometry.location,
              title: place.name,
            });
            marker.addListener("click", () => {
              infowindow.setContent(`<strong>${place.name}</strong><br>${place.formatted_address}`);
              infowindow.open(map, marker);
            });
          });
        } else {
          alert("No venues found.");
        }
      });
    }