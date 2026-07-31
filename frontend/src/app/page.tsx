async function getDashboard() {
  const response = await fetch(
    "http://localhost:8000/clients/1/dashboard",
    {
      cache: "no-store"
    }
  );

  return response.json();
}


export default async function Home() {

  const dashboard = await getDashboard();


  return (
    <main className="p-10">

      <h1 className="text-3xl font-bold">
        {dashboard.name}
      </h1>


      <div className="mt-6 rounded-xl border p-6">

        <h2 className="text-lg">
          Total Assets
        </h2>

        <p className="text-4xl font-bold">
          {dashboard.total_assets}
        </p>

      </div>


      <h2 className="mt-10 text-2xl font-bold">
        Institutions
      </h2>


      {dashboard.institutions.map(
        (institution:any)=>(
          
          <div
            key={institution.id}
            className="mt-5 rounded-xl border p-5"
          >

            <h3 className="text-xl font-semibold">
              {institution.name}
            </h3>


            {institution.accounts.map(
              (account:any)=>(
                
                <div
                  key={account.id}
                  className="mt-4"
                >

                  <p className="font-medium">
                    {account.name}
                  </p>

                  <p>
                    Balance:
                    {" "}
                    {account.balance}
                    {" "}
                    {account.currency}
                  </p>


                  <ul className="ml-5 mt-2 list-disc">

                    {account.positions.map(
                      (position:any)=>(
                        
                        <li key={position.security_name}>
                          {position.security_name}
                          :
                          {" "}
                          {position.market_value}
                          {" "}
                          {position.currency}
                        </li>

                      )
                    )}

                  </ul>

                </div>

              )
            )}

          </div>

        )
      )}

    </main>
  );
}