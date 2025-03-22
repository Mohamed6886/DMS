import psycopg2
from psycopg2 import OperationalError, DatabaseError
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

DATABASE_URL = "postgresql://flower_db_owner:npg_51HLIvYdpuVQ@ep-green-block-a8ifhr0o-pooler.eastus2.azure.neon.tech/flower_db?sslmode=require"

# Database connection details
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM team9_flowers ORDER BY id;")
                flowers = cur.fetchall()
        return render_template('flowers.html', flowers=flowers) #Refers to our flowers.html file. 
    except (OperationalError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 500

# Get all flowers and update water levels
@app.route('/team9_flowers', methods=['GET'])
def get_flowers():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Now fetch all flowers to display
                cur.execute("SELECT * FROM team9_flowers ORDER BY id;")
                flowers = cur.fetchall()
                
        return jsonify([{
            "id": f[0],
            "name": f[1],
            "last_watered": f[2].strftime("%Y-%m-%d"),
            "water_level": f[3],
            "min_water_required": f[4],
            "needs_water": f[5]  # Including the needs_water status
        } for f in flowers])
    except (OperationalError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 500



@app.route('/add_team9_flowers', methods=['POST'])
def add_flower():
    # Extract data from the incoming JSON request
    data = request.json
    name = data.get('name')
    last_watered = data.get('last_watered')
    water_level = data.get('water_level')
    min_water_required = data.get('min_water_required')

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Insert the new flower and retrieve the id of the newly added flower
                cur.execute("""
                    INSERT INTO team9_flowers 
                    (name, last_watered, water_level, min_water_required) 
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (name, last_watered, water_level, min_water_required))

                # Fetch the id of the newly inserted flower
                new_flower_id = cur.fetchone()[0]

                # Now, update the water level for just the newly added flower
                cur.execute("""
                    UPDATE team9_flowers
                    SET water_level = water_level - (5 * (CURRENT_DATE - last_watered))
                    WHERE id = %s
                """, (new_flower_id,))

                conn.commit()  # Commit the transaction to insert the flower and update water level

        return jsonify({"message": "Flower added successfully!"})
    except (OperationalError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 500


@app.route('/team9_flowers/<int:id>', methods=['PUT'])
def update_flower(id):
    data = request.json
    
    # Ensure we have the correct values
    if not data.get('last_watered') or not data.get('water_level'):
        return jsonify({"error": "Invalid input, 'last_watered' and 'water_level' are required."}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Log the id being updated and the data being used
                print(f"Updating flower with ID: {id}")
                print(f"New data: last_watered={data['last_watered']}, water_level={data['water_level']}")

                # Perform the update for last_watered and water_level
                cur.execute("""
                    UPDATE team9_flowers 
                    SET last_watered = %s, water_level = %s 
                    WHERE id = %s
                """, (data['last_watered'], data['water_level'], id))

                # Now, update the water_level based on the new last_watered date
                cur.execute("""
                    UPDATE team9_flowers
                    SET water_level = water_level - (5 * (CURRENT_DATE - last_watered))
                    WHERE id = %s
                """, (id,))  # Pass the specific id of the flower being updated

                conn.commit()  # Commit the transaction

        return jsonify({"message": "Flower updated successfully!"})
    except (OperationalError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 500



# Delete a flower by ID
@app.route('/team9_flowers/<int:id>', methods=['DELETE'])
def delete_flower(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM team9_flowers WHERE id = %s", (id,))
        return jsonify({"message": "Flower deleted successfully!"})
    except (OperationalError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)






