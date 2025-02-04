// Create temp.js
db = db.getSiblingDB('laptop_analyzer');
db.createCollection('laptops');

let data = cat('/data/data.csv').split('\n');
let documents = data.slice(1).map(line => {
    let fields = line.split(',');
    return {
        url: fields[0],
        title: fields[1],
        price: parseFloat(fields[2]) || 0,
        brand: fields[3],
        ram: fields[4],
        cpu_brand: fields[5],
        cpu_model: fields[6],
        gpu_model: fields[7],
        gpu_brand: fields[8],
        display_size: fields[9],
        refresh_rate: fields[10],
        resolution: fields[11],
        storage: fields[12]
    };
});

db.laptops.insertMany(documents);